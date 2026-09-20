@file:UseSerializers(UuidSerializer::class, URLSerializer::class)
@file:OptIn(ExperimentalUuidApi::class, ExperimentalTime::class)

package hu.bme.mit.ftsrg.dva.log

import hu.bme.mit.ftsrg.dva.dto.processing.EvaluationResult
import hu.bme.mit.ftsrg.serialization.URLSerializer
import hu.bme.mit.ftsrg.serialization.UuidSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import kotlinx.serialization.json.JsonElement
import kotlin.time.ExperimentalTime
import kotlin.time.Instant
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@Serializable
data class RequestLog(
    val id: Uuid = Uuid.random(),
    val type: RequestType,
    val exchangeID: Uuid,
    val contractID: Uuid,
    val vlaID: Uuid,
    val data: JsonElement,
    val evaluationPassing: Boolean,
    val evaluationResults: List<EvaluationResult>,
    val receivedDate: Instant,
    val vcID: Uuid? = null,
    val error: RequestLogError? = null
)

@Serializable
enum class RequestType { ATTESTATION_REQUEST, PROOF_REQUEST }

@Serializable
data class RequestLogError(val title: String, val detail: String? = null)