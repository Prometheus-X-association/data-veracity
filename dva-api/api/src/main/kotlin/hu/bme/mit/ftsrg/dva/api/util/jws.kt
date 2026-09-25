@file:OptIn(ExperimentalUuidApi::class, ExperimentalEncodingApi::class)

package hu.bme.mit.ftsrg.dva.api.util

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlin.io.encoding.Base64
import kotlin.io.encoding.ExperimentalEncodingApi
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

private val base64Url = Base64.UrlSafe.withPadding(Base64.PaddingOption.ABSENT_OPTIONAL)

/**
 * The ID of the AoV credential in a compact JWS issued by the VC Manager: its
 * `credentialSubject.vc_id` claim. Only reads the payload; the signature is
 * the VC Manager's own, so it is not checked here.
 *
 * @throws IllegalArgumentException if the JWS carries no readable credential ID.
 */
fun vcIDOf(jws: String): Uuid {
    val payload = jws.split('.').takeIf { it.size == 3 }?.get(1)
        ?: throw IllegalArgumentException("not a compact JWS")
    val claims = Json.parseToJsonElement(base64Url.decode(payload).decodeToString()).jsonObject
    val vcID = claims["credentialSubject"]?.jsonObject?.get("vc_id")?.jsonPrimitive?.content
        ?: throw IllegalArgumentException("no credentialSubject.vc_id claim")
    return Uuid.parse(vcID)
}
