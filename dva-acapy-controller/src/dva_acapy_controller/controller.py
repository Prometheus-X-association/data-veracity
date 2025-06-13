import requests
import json

from asyncio import Queue, CancelledError
from datetime import datetime
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from httpx import AsyncClient
from pathlib import Path
from time import sleep
from typing import Dict, Any
from uuid import uuid4

from fastapi import (
    FastAPI,
    Request,
    Body,
    HTTPException,
    Query,
)

from .aov import AOV, AOVRequest
from .config import (
    ADMIN_URL,
    ADMIN_LABEL,
    PEER_AGENT_URL,
    PEER_CONTROLLER_URL,
    PEER_CONTROLLER_PORT_IN,
    PEER_CONTROLLER_PORT_OUT,
    PEER_LABEL,
    LOG_FILE,
)


app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

webhook_logs = []
presentation_queue = Queue()

SELF_CONNECTION_ID = None
SELF_SCHEMA_ID = None
SELF_CRED_DEF_ID = None


@app.on_event("startup")
async def startup_event():
    print(f"{ADMIN_LABEL} Controller is starting...")
    await presentation_queue.put({"message": "Startup test data!"})


@app.on_event("shutdown")
async def shutdown_event():
    print(f"{ADMIN_LABEL} Controller is shutting down...")
    if webhook_logs:
        with open("log_human_readable.json", "w") as f:
            json.dump(webhook_logs, f, indent=2)


@app.get("/", response_class=HTMLResponse)
async def root():
    html = Path("static/index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)


# Helper function: wait until connection is active
def wait_until_connection_active(admin_url, conn_id, timeout=10):
    for _ in range(timeout):
        conns = requests.get(f"{admin_url}/connections").json()["results"]
        conn = next((c for c in conns if c["connection_id"] == conn_id), None)
        if conn and conn["state"] == "active":
            return True
        sleep(1)
    return False


@app.post("/webhooks/topic/{topic}/")
async def webhook_listener(topic: str, request: Request):
    data = await request.json()
    data["source"] = ADMIN_LABEL
    webhook_logs.append({"topic": topic, "data": data})
    with open(LOG_FILE, "w") as f:
        json.dump(webhook_logs, f, indent=2)
    await presentation_queue.put(data)
    print(f"Webhook received on topic: {topic}")
    return {"status": "received"}


@app.post("/webhooks/topic/present_proof_v2_0/")
async def handle_presentation_webhook(request: Request):
    data = await request.json()
    print(f"[{ADMIN_LABEL}] Presentation webhook received:")
    print(json.dumps(data, indent=2))

    state = data.get("state")
    if state in ["presentation-received", "verified"]:
        await presentation_queue.put(data)

    return {"status": "received"}


@app.get("/connections/self")
async def get_self_connection():
    global SELF_CONNECTION_ID
    if not SELF_CONNECTION_ID:
        return {"error": "Self-connection not initialized."}
    return {"self_connection_id": SELF_CONNECTION_ID}


@app.post("/init_all_self")
async def init_all_self():
    global SELF_CONNECTION_ID, SELF_SCHEMA_ID, SELF_CRED_DEF_ID

    # Step 1: Create Invitation for self-connection
    invitation_resp = requests.post(
        f"{ADMIN_URL}/out-of-band/create-invitation",
        json={
            "handshake_protocols": ["https://didcomm.org/didexchange/1.0"],
            "use_public_did": False,
        },
    )
    if invitation_resp.status_code != 200:
        return {
            "error": "Failed to create self-invitation",
            "details": invitation_resp.text,
        }

    invitation = invitation_resp.json()["invitation"]

    # Step 2: Receive own invitation
    receive_resp = requests.post(
        f"{ADMIN_URL}/out-of-band/receive-invitation",
        json=invitation,
    )
    if receive_resp.status_code != 200:
        return {
            "error": "Failed to accept own invitation",
            "details": receive_resp.text,
        }

    conn_id = receive_resp.json()["connection_id"]

    # Step 3: Wait until connection is active
    if not wait_until_connection_active(f"{ADMIN_URL}/", conn_id):
        return {"error": "Self connection did not become active"}

    SELF_CONNECTION_ID = conn_id

    # Step 4: Create Self-Identity Schema
    schema_resp = requests.post(
        f"{ADMIN_URL}/schemas",
        json={
            "schema_name": f"Self-Identity-{uuid4().hex[:6]}",
            "schema_version": "1.0",
            "attributes": [
                "vc_id",
                "valid_since",
                "subject",
                "issuer_id",
                "record_id",
                "contract_id",
                "payload",
            ],
        },
    )
    if schema_resp.status_code != 200:
        return {
            "error": "Failed to create Self-Identity schema",
            "details": schema_resp.text,
        }

    SELF_SCHEMA_ID = schema_resp.json().get("schema_id")

    # Step 5: Create Credential Definition
    cred_def_resp = requests.post(
        f"{ADMIN_URL}/credential-definitions",
        json={
            "schema_id": SELF_SCHEMA_ID,
            "support_revocation": False,
            "tag": "self-identity",
        },
    )
    if cred_def_resp.status_code != 200:
        return {
            "error": "Failed to create Self-Identity credential definition",
            "details": cred_def_resp.text,
        }

    SELF_CRED_DEF_ID = cred_def_resp.json().get("credential_definition_id")

    with open("cred_def.json", "w") as f:
        json.dump({"cred_def_id": SELF_CRED_DEF_ID}, f)

    # Step 6: Self-Issue Credential to Own Wallet
    cred_attrs = {
        "vc_id": str(uuid4()),
        "valid_since": datetime.utcnow().isoformat(),
        "subject": "Provider Subject",
        "issuer_id": "Provider",
        "record_id": str(uuid4()),
        "contract_id": "contract123",
        "payload": "[]",
    }

    issue_payload = {
        "connection_id": SELF_CONNECTION_ID,
        "credential_preview": {
            "@type": "issue-credential/2.0/credential-preview",
            "attributes": [{"name": k, "value": v} for k, v in cred_attrs.items()],
        },
        "filter": {"indy": {"cred_def_id": SELF_CRED_DEF_ID}},
    }

    issue_resp = requests.post(
        f"{ADMIN_URL}/issue-credential-2.0/send-offer", json=issue_payload
    )
    if issue_resp.status_code != 200:
        return {
            "error": "Failed to self-issue credential",
            "details": issue_resp.text,
        }

    return {
        "message": "Self-connection, schema, credential definition, and self-credential issued successfully.",
        "self_connection_id": SELF_CONNECTION_ID,
        "self_schema_id": SELF_SCHEMA_ID,
        "self_cred_def_id": SELF_CRED_DEF_ID,
    }


@app.post("/generate_aov")
async def generate_aov(payload: AOVRequest):
    global SELF_CONNECTION_ID, SELF_CRED_DEF_ID

    payload_str = json.dumps(payload.payload, indent=2)

    record = AOV(
        vc_id=str(uuid4()),
        valid_since=datetime.utcnow(),
        subject=payload.subject,
        issuer_id=payload.issuer_id,
        record_id=str(uuid4()),
        contract_id=uuid4().hex,
        payload=payload_str,
    )

    target = payload.target
    if target not in ["self", PEER_LABEL]:
        raise HTTPException(status_code=400, detail="Invalid target")

    if target == "self":
        if not SELF_CONNECTION_ID or not SELF_CRED_DEF_ID:
            raise HTTPException(
                status_code=400,
                detail="Self connection or credential definition not initialized",
            )
        connection_id = SELF_CONNECTION_ID
        cred_def_id = SELF_CRED_DEF_ID
    else:
        conns = requests.get(f"{ADMIN_URL}/connections").json()["results"]
        peer_conn = next(
            (c for c in conns if c["connection_id"] != SELF_CONNECTION_ID),
            None,
        )
        if not peer_conn:
            raise HTTPException(
                status_code=400, detail=f"No {PEER_LABEL} connection found"
            )
        connection_id = peer_conn["connection_id"]

        try:
            with open("cred_def.txt", "r") as f:
                cred_def_data = json.load(f)
            cred_def_id = cred_def_data["cred_def_id"]
        except Exception:
            raise HTTPException(
                status_code=500, detail="Missing or invalid credential definition file"
            )

    cred_attrs = {
        "vc_id": record.vc_id,
        "valid_since": record.valid_since.isoformat(),
        "subject": record.subject,
        "issuer_id": record.issuer_id,
        "record_id": record.record_id,
        "contract_id": record.contract_id,
        "payload": record.payload,
    }

    issue_payload = {
        "connection_id": connection_id,
        "credential_preview": {
            "@type": "issue-credential/2.0/credential-preview",
            "attributes": [{"name": k, "value": v} for k, v in cred_attrs.items()],
        },
        "filter": {"indy": {"cred_def_id": cred_def_id}},
    }

    issue_resp = requests.post(
        f"{ADMIN_URL}/issue-credential-2.0/send", json=issue_payload
    )
    print(f"Issue response: {issue_resp}")

    if issue_resp.status_code != 200:
        return {"error": "Credential issue failed", "details": issue_resp.text}

    if target == f"{PEER_LABEL}":
        try:
            forward_resp = requests.post(
                f"{PEER_CONTROLLER_URL}:{PEER_CONTROLLER_PORT_OUT}/receive_aov",
                json={"source": "provider", "credential": cred_attrs},
            )
            forward_resp.raise_for_status()
            print(f"Forwarded VC to {PEER_LABEL} UI stream.")
        except Exception as e:
            print(f"Failed to forward VC to {PEER_LABEL} UI: {e}")
    return {"message": f"AOV issued to {target}", "credential_data": cred_attrs}


@app.post("/request_presentation_from_peer")
async def request_presentation_from_peer():
    conns = requests.get(f"{ADMIN_URL}/connections").json().get("results", [])
    consumer_conn = next(
        (
            c
            for c in conns
            if c["state"] == "active"
            and c.get("their_label", "").lower() == PEER_LABEL.lower()
        ),
        None,
    )

    if not consumer_conn:
        create_inv_resp = requests.post(
            f"{ADMIN_URL}/out-of-band/create-invitation",
            json={
                "handshake_protocols": ["https://didcomm.org/didexchange/1.0"],
                "use_public_did": False,
            },
        )
        if create_inv_resp.status_code != 200:
            raise HTTPException(
                status_code=500, detail="Failed to create invitation on Consumer ACA-Py"
            )

        invitation = create_inv_resp.json().get("invitation")
        if not invitation:
            raise HTTPException(
                status_code=500, detail="No invitation returned by Consumer ACA-Py"
            )

        provider_agent_host = PEER_AGENT_URL
        provider_admin = f"{provider_agent_host}:{PEER_CONTROLLER_PORT_IN}"

        receive_inv_resp = requests.post(
            f"{provider_admin}/out-of-band/receive-invitation", json=invitation
        )
        if receive_inv_resp.status_code != 200:
            raise HTTPException(
                status_code=500, detail="Failed to send invitation to Provider ACA-Py"
            )

        consumer_active = False
        for _ in range(15):
            conns = requests.get(f"{ADMIN_URL}/connections").json().get("results", [])
            consumer_conn = next(
                (
                    c
                    for c in conns
                    if c["state"] == "active"
                    and c.get("their_label", "").lower() == PEER_LABEL.lower()
                ),
                None,
            )
            if consumer_conn:
                consumer_active = True
                break
            sleep(1)

        if not consumer_active:
            raise HTTPException(
                status_code=500,
                detail="Consumer connection did not become active in time",
            )

    provider_agent_host = PEER_AGENT_URL
    provider_admin = f"{provider_agent_host}:{PEER_CONTROLLER_PORT_IN}"

    provider_active = False
    provider_conn = None
    for _ in range(15):
        resp = requests.get(f"{provider_admin}/connections")
        if resp.status_code == 200:
            prow = resp.json().get("results", [])
            provider_conn = next(
                (
                    c
                    for c in prow
                    if c.get("their_label", "").lower() == ADMIN_LABEL.lower()
                    and c.get("state") == "active"
                ),
                None,
            )
            if provider_conn:
                provider_active = True
                break
        sleep(1)

    if not provider_active or not provider_conn:
        raise HTTPException(
            status_code=500, detail="Provider connection did not become active in time"
        )

    provider_connection_id = provider_conn.get("connection_id")

    pres_request = {
        "connection_id": provider_connection_id,
        "presentation_request": {
            "indy": {
                "name": "PleasePresentAOV",
                "version": "1.0",
                "requested_attributes": {
                    "attr_subject": {"name": "subject", "restrictions": [{}]},
                    "attr_issuer_id": {"name": "issuer_id", "restrictions": [{}]},
                    "attr_vc_id": {"name": "vc_id", "restrictions": [{}]},
                    "attr_valid_since": {"name": "valid_since", "restrictions": [{}]},
                    "attr_record_id": {"name": "record_id", "restrictions": [{}]},
                    "attr_contract_id": {"name": "contract_id", "restrictions": [{}]},
                    "attr_payload": {"name": "payload", "restrictions": [{}]},
                },
                "requested_predicates": {},
            }
        },
    }

    resp = requests.post(
        f"{provider_admin}/present-proof-2.0/send-request", json=pres_request
    )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=500, detail="Failed to send proof request to Provider ACA-Py"
        )
    resp.raise_for_status()
    data = resp.json()

    return {"message": "Presentation request sent to provider.", "aov": data}


@app.get("/request_aov")
async def request_aov(
    subject: str = Query("{ADMIN_LABEL} App"),
    issuer_id: str = Query(f"{ADMIN_LABEL}"),
    comment: str = Query("Requested dynamically"),
):
    params = {
        "subject": subject,
        "issuer_id": issuer_id,
        "comment": comment,
        "target": f"{PEER_LABEL}",
    }
    async with AsyncClient() as client:
        resp = await client.post(
            f"{PEER_CONTROLLER_URL}:{PEER_CONTROLLER_PORT_OUT}/generate_aov",
            params=params,
            timeout=10.0,
        )
    resp.raise_for_status()
    data = resp.json()
    vc = data.get("credential_data", {})
    await presentation_queue.put(vc)
    return {"received_vc": vc}


@app.post("/receive_aov")
async def receive_aov(aov: Dict[str, Any] = Body(...)):
    print("Received AOV from consumer:")
    print(json.dumps(aov, indent=2))

    return {"message": "AOV received by provider", "aov": aov}


@app.post("/present_aov")
async def present_custom_vc():
    # Search for active connection to consumer
    conns = requests.get(f"{ADMIN_URL}/connections").json()["results"]
    peer_conn = next((c for c in conns if c["state"] == "active"), None)
    if not peer_conn:
        raise HTTPException(
            status_code=400,
            detail=f"No active connection found with peer '{PEER_LABEL}'.",
        )

    connection_id = peer_conn["connection_id"]

    # Build presentation request with restrictions
    pres_request = {
        "connection_id": connection_id,
        "presentation_request": {
            "indy": {
                "name": "PleasePresentAOV",
                "version": "1.0",
                "requested_attributes": {
                    "attr_subject": {"name": "subject", "restrictions": [{}]},
                    "attr_issuer_id": {"name": "issuer_id", "restrictions": [{}]},
                    "attr_vc_id": {"name": "vc_id", "restrictions": [{}]},
                    "attr_valid_since": {"name": "valid_since", "restrictions": [{}]},
                    "attr_record_id": {"name": "record_id", "restrictions": [{}]},
                    "attr_contract_id": {"name": "contract_id", "restrictions": [{}]},
                    "attr_payload": {"name": "payload", "restrictions": [{}]},
                },
                "requested_predicates": {},
            }
        },
    }

    resp = requests.post(
        f"{ADMIN_URL}/present-proof-2.0/send-request", json=pres_request
    )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=500, detail="Failed to send proof request via ACA-Py"
        )

    return {
        "message": "Presentation request sent from provider to consumer.",
        "connection_id": connection_id,
    }


@app.get("/events/")
async def events():
    async def event_generator():
        while True:
            try:
                event = await presentation_queue.get()
                event_source = event.get("source")
                if event_source is None:
                    event_source = ADMIN_LABEL
                yield f"data: {json.dumps(event)}\n\n"
            except CancelledError:
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")
