@file:UseSerializers(URLSerializer::class)

package hu.bme.mit.ftsrg.dva.dto.aov

import hu.bme.mit.ftsrg.dva.model.aov.AttestationOfVeracity
import hu.bme.mit.ftsrg.serialization.java.URLSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import java.net.URL

@Serializable
data class AttestationVerificationRequestDTO(
  val id: String? = null,
  val aov: AttestationOfVeracity,
  val callbackURL: URL,
)
