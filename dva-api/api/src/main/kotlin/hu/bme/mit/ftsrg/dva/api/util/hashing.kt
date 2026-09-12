package hu.bme.mit.ftsrg.dva.api.util

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import java.security.MessageDigest

fun hash(data: JsonElement): String {
    val preimage: ByteArray = data.canonical().toString().toByteArray(Charsets.UTF_8)
    val hash: ByteArray = MessageDigest.getInstance("SHA-256").digest(preimage)
    return hash.toHexString()
}

fun JsonElement.canonical(): JsonElement = when (this) {
    is JsonObject -> JsonObject(entries.sortedBy { it.key }.associate { it.key to it.value.canonical() })
    is JsonArray -> JsonArray(map { it.canonical() })
    is JsonPrimitive -> this
}