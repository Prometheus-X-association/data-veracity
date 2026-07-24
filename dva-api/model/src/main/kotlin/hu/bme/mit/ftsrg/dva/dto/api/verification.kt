package hu.bme.mit.ftsrg.dva.dto.api

import kotlinx.serialization.Serializable

@Serializable
data class AttestationVerificationRequest(
    val jws: String,
)

@Serializable
data class AttestationVerificationResponse(
    val verified: Boolean,
    val reason: String? = null,
)
