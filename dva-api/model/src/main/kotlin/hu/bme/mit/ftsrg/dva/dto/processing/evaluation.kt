package hu.bme.mit.ftsrg.dva.dto.processing

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

@Serializable
data class EvaluateBatchRequest(
    val vla: JsonObject,
    val data: JsonElement,
)

@OptIn(ExperimentalTime::class)
@Serializable
data class EvaluationResult(
    val engine: String,
    val timestamp: Instant,
    val success: Boolean,
    val details: String? = null,
    val error: String? = null,
)

