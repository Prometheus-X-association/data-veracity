@file:OptIn(ExperimentalUuidApi::class)

package hu.bme.mit.ftsrg.dva.dto.vcmanager

import hu.bme.mit.ftsrg.dva.dto.processing.EvaluationResult
import kotlinx.serialization.Serializable
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@Serializable
data class AoVIssueRequest(
    val subject: String,
    val contractId: Uuid,
    val dataExchangeId: Uuid,
    val evaluationResults: List<EvaluationResult>,
)

@Serializable
data class AoVIssueResponse(
    val jws: String,
    val vcID: Uuid,
)
