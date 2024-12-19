package hu.bme.mit.ftsrg.vc.model

import java.time.ZonedDateTime

/**
 * Dummy W3C Verifiable Credential class.
 */
data class VerifiableCredential(
  override val id: String,
  override val type: String,
  override val validFrom: ZonedDateTime,
  override val subject: CredentialSubject,
  override val issuer: String
) : IVerifiableCredential