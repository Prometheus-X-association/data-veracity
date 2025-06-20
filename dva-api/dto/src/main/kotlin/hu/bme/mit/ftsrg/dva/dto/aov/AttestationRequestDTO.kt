package hu.bme.mit.ftsrg.dva.dto.aov

import hu.bme.mit.ftsrg.contractmanager.contract.model.Contract
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement

@Serializable
data class AttestationRequestDTO(
  val id: String? = null,
  val exchangeID: String,
  val contract: Contract,
  val data: JsonElement,
  val attesterID: String,
)