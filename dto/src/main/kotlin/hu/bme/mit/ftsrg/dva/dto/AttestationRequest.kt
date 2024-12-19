package hu.bme.mit.ftsrg.dva.dto

import hu.bme.mit.ftsrg.contractmanager.contract.model.Contract
import kotlinx.serialization.Contextual
import kotlinx.serialization.Serializable
import java.net.URL

@Serializable
data class AttestationRequest(
  val id: String? = null,
  @Contextual val contract: Contract,
  val data: ByteArray,
  val attesterID: String,
  @Contextual val callbackURL: URL,
)
