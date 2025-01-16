@file:UseSerializers(ZonedDateTimeSerializer::class)

package hu.bme.mit.ftsrg.vc.model

import hu.bme.mit.ftsrg.serialization.ZonedDateTimeSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import java.time.ZonedDateTime

/**
 * Dummy W3C Verifiable Credential class.
 */
@Serializable
data class VerifiableCredential(
  override val id: String,
  override val type: String,
  override val validFrom: ZonedDateTime,
  override val subject: CredentialSubject,
  override val issuer: String
) : IVerifiableCredential