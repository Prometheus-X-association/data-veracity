package hu.bme.mit.ftsrg.vc.model

import kotlinx.serialization.Serializable

/**
 * Dummy W3C verifiable credential subject representation.
 */
@Serializable
data class CredentialSubject(val id: String)
