"""
FastAPI routes for the DVA VC Manager.

Two AoV endpoints called by the DVA API during the synchronous
attestation flow:

* ``POST /aov/issue`` — called by the DVA API during credential
  issuance with the seven claims + the veracity-check results array.
  Generates a UUID for the credential, signs the JWS, and returns
  only the compact JWS string (issuer did:key, vc_id, and issuance
  date are all encoded in the JWS itself).
* ``POST /aov/verify`` — called by the DVA API at the consumer side to
  verify a JWS. The issuer ``did:key`` is extracted from the JWS
  payload and looked up in the whitelist. Fail-closed: rejects if the
  whitelist is empty or the issuer is not registered.

Plus four admin endpoints:

* ``GET /admin/whitelist`` — list trusted attesters.
* ``POST /admin/whitelist`` — register a trusted attester's did:key.
* ``DELETE /admin/whitelist/{did_key}`` — remove an attester.
* ``GET /admin/keys`` — view this service's own issuer did:key
  (read-only; no private key bytes exposed).
"""

from __future__ import annotations

import urllib.parse
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from .audit import AuditRepo, CredentialAudit, VerificationAudit
from .dependencies import get_audit, get_key_store, get_whitelist
from .did_key import did_key_to_public_key
from .keys import SigningKeyStore
from .models import (
    AovIssueRequest,
    AovIssueResponse,
    AovVerifyRequest,
    AovVerifyResponse,
    CredentialAuditDTO,
    OwnKeyDTO,
    VerificationAuditDTO,
    WhitelistAddRequest,
    WhitelistEntryDTO,
)
from .signing import (
    AovClaims,
    MalformedJws,
    decode_payload,
    sign_jws,
    split_jws,
    verify_jws,
)
from .whitelist import WhitelistEntry, WhitelistRepo

router = APIRouter()


@router.post("/aov/issue", response_model=AovIssueResponse)
async def aov_issue(
    req: AovIssueRequest,
    key_store: SigningKeyStore = Depends(get_key_store),
    audit: AuditRepo = Depends(get_audit),
) -> AovIssueResponse:
    """Issue an AoV JWS credential from the veracity-check results."""
    signing_key = key_store.load_or_generate()
    issuer_did_key = key_store.issuer_did_key()

    # build_aov_payload embeds these values into the VC JSON-LD payload.
    # Note the credentialSubject keys stay snake_case even though the
    # request body is camelCase -- see the models module docstring.
    claims = AovClaims(
        vc_id=str(uuid4()),
        valid_since=req.valid_since,
        subject=req.subject,
        issuer_id=req.issuer_id,
        record_id=req.record_id,
        contract_id=req.contract_id,
        data_exchange_id=req.data_exchange_id,
        payload=req.payload,
    )
    jws = sign_jws(claims, signing_key, issuer_did_key)
    await audit.record_credential(
        credential_id=claims.vc_id,
        jws=jws,
        request=req.model_dump(mode="json", by_alias=True),
    )
    return AovIssueResponse(jws=jws)


@router.post("/aov/verify", response_model=AovVerifyResponse)
async def aov_verify(
    req: AovVerifyRequest,
    whitelist: WhitelistRepo = Depends(get_whitelist),
    audit: AuditRepo = Depends(get_audit),
) -> AovVerifyResponse:
    """
    Verify an AoV JWS.

    The issuer did:key is extracted from the JWS
    payload and looked up in the whitelist.
    """

    request = req.model_dump(mode="json", by_alias=True)

    async def audited_response(
        verified: bool,
        reason: str | None = None,
        status_code: int = 200,
        body: dict[str, object] | None = None,
    ) -> AovVerifyResponse:
        response = AovVerifyResponse(verified=verified, reason=reason)
        await audit.record_verification(
            request=request,
            response={
                "status_code": status_code,
                **(body if body is not None else response.model_dump(exclude_none=True)),
            },
        )
        return response

    # 1. Structural check: must be a 3-part compact JWS.
    try:
        split_jws(req.jws)
    except MalformedJws as e:
        await audited_response(
            False,
            str(e),
            status.HTTP_400_BAD_REQUEST,
            body={"detail": str(e)},
        )
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    # 2. Whitelist must be non-empty. Checked early so an operator who
    # has not configured any trusted issuers gets a clear reason rather
    # than a payload-decode error.
    entries = await whitelist.all()
    if not entries:
        return await audited_response(
            False, "whitelist is not configured; verification is disabled"
        )

    # 3. Decode the JWS payload to extract the issuer did:key. A payload
    # that is structurally a JWS but cannot be decoded (e.g. tampered)
    # is reported as a verification failure, not a 400.
    try:
        payload = decode_payload(req.jws)
    except ValueError as e:
        return await audited_response(False, f"malformed JWS payload: {e}")

    issuer_did_key = payload.get("issuer")
    if not isinstance(issuer_did_key, str) or not issuer_did_key:
        return await audited_response(False, "JWS payload missing issuer")

    # 4. Issuer must be whitelisted
    entry = await whitelist.find(issuer_did_key)
    if entry is None:
        return await audited_response(False, "issuer not whitelisted")

    # 5. Derive the public key from the whitelist record's did:key.
    try:
        public_key = did_key_to_public_key(entry.did_key)
    except ValueError as e:
        return await audited_response(
            False, f"whitelist entry contains invalid did:key: {e}"
        )

    # 6. Verify the Ed25519 signature.  A structurally-valid JWS whose
    # signature does not verify returns verified=false.
    try:
        ok = verify_jws(req.jws, public_key)
    except ValueError as e:
        return await audited_response(False, f"signature check failed: {e}")

    if not ok:
        return await audited_response(False, "signature mismatch")

    return await audited_response(True)


# --- Admin ------------------------------------------------------------


admin_router = APIRouter()


@admin_router.get("/admin/whitelist", response_model=list[WhitelistEntryDTO])
async def whitelist_list(
    whitelist: WhitelistRepo = Depends(get_whitelist),
) -> list[WhitelistEntry]:
    return await whitelist.all()


@admin_router.post(
    "/admin/whitelist",
    status_code=status.HTTP_201_CREATED,
    response_model=WhitelistEntryDTO,
)
async def whitelist_add(
    req: WhitelistAddRequest,
    whitelist: WhitelistRepo = Depends(get_whitelist),
) -> WhitelistEntry:
    return await whitelist.add(req.did_key, req.label)


@admin_router.delete(
    "/admin/whitelist/{did_key}", status_code=status.HTTP_204_NO_CONTENT
)
async def whitelist_remove(
    did_key: str,
    whitelist: WhitelistRepo = Depends(get_whitelist),
) -> None:
    # URL-decode in case the path contains special chars (did:key contains ':').
    decoded = urllib.parse.unquote(did_key)
    removed = await whitelist.remove(decoded)
    if not removed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "did:key not in whitelist")
    return None


@admin_router.get("/admin/keys", response_model=OwnKeyDTO)
async def keys_view(
    key_store: SigningKeyStore = Depends(get_key_store),
) -> OwnKeyDTO:
    return OwnKeyDTO(
        issuer_did_key=key_store.issuer_did_key(), key_path=str(key_store.path)
    )


@admin_router.get("/admin/credentials", response_model=list[CredentialAuditDTO])
async def credentials_list(
    audit: AuditRepo = Depends(get_audit),
) -> list[CredentialAudit]:
    """Return every credential this VC manager issued, newest first."""
    return await audit.credentials()


@admin_router.get("/admin/verifications", response_model=list[VerificationAuditDTO])
async def verifications_list(
    audit: AuditRepo = Depends(get_audit),
) -> list[VerificationAudit]:
    """Return every verification request and outcome, newest first."""
    return await audit.verifications()
