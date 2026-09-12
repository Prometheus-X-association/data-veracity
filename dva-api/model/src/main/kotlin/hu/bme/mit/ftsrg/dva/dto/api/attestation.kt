@file:UseSerializers(URLSerializer::class)

package hu.bme.mit.ftsrg.dva.dto.api

import hu.bme.mit.ftsrg.dva.dto.processing.EvaluationResult
import hu.bme.mit.ftsrg.serialization.URLSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import kotlinx.serialization.json.JsonElement
import java.net.URL
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class)
@Serializable
data class AttestationRequest(
    val id: String? = null,
    val exchangeID: Uuid,
    val contractID: Uuid,
    val vlaID: Uuid,
    val data: JsonElement,
)

@Serializable
data class AttestationResponse(
    val jws: String? = null,
    val evaluationPassing: Boolean,
    val evaluationResults: List<EvaluationResult>,
)


@Serializable
data class AttestationVerificationRequestDTO(
    val id: String? = null,
    val exchangeID: String,
    val contractID: String,
    val attesterAgentURL: URL,
    val attesterAgentLabel: String
)