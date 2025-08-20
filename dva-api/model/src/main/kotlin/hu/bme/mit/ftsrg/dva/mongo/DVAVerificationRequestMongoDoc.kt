@file:UseSerializers(URLSerializer::class)

package hu.bme.mit.ftsrg.dva.mongo

import hu.bme.mit.ftsrg.serialization.URLSerializer
import kotlinx.datetime.Instant
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import kotlinx.serialization.json.JsonObject
import java.net.URL

@Serializable
data class DVAVerificationRequestMongoDoc(
    val requestID: String?,
    val exchangeID: String,
    val contractID: String,
    val attesterAgentURL: URL,
    val attesterAgentLabel: String,
    val requestedAt: Instant,
    val verifiedAt: Instant? = null,
    val verified: Boolean = false,
    val presentationRequestData: JsonObject? = null,
)