package hu.bme.mit.ftsrg.dva.dto.common

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class HealthStatus {
    @SerialName("pass")
    PASS,

    @SerialName("warn")
    WARN,

    @SerialName("fail")
    FAIL,
}

@Serializable
data class Health(val status: HealthStatus, val output: String? = null)