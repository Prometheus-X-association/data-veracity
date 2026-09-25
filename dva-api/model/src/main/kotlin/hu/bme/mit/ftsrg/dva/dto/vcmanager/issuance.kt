@file:OptIn(ExperimentalUuidApi::class, ExperimentalTime::class)

package hu.bme.mit.ftsrg.dva.dto.vcmanager

import hu.bme.mit.ftsrg.dva.dto.processing.EvaluationResult
import kotlinx.serialization.Serializable
import kotlin.time.ExperimentalTime
import kotlin.time.Instant
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

/** Body of the VC Manager's `POST /aov/issue`: the AoV claims (see `docs/spec/dva-vc-manager.yaml`). */
@Serializable
data class AoVIssueRequest(
    val validSince: Instant,
    val subject: String,
    val issuerId: String,
    val recordId: String,
    val contractId: Uuid,
    val dataExchangeId: Uuid,
    val payload: String,
    val evaluationResults: List<EvaluationResult>,
)

/** The VC Manager answers with the JWS alone; the credential's ID is a claim inside it. */
@Serializable
data class AoVIssueResponse(
    val jws: String,
)
