@file:UseSerializers(URLSerializer::class)

package hu.bme.mit.ftsrg.dva.dto.aov

import hu.bme.mit.ftsrg.contractmanager.contract.model.Contract
import hu.bme.mit.ftsrg.serialization.java.URLSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import java.net.URL

@Serializable
data class AttestationRequestDTO(
  val id: String? = null,
  val contract: Contract,
  val data: ByteArray,
  val attesterID: String,
  val callbackURL: URL
)