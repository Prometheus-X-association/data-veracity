package hu.bme.mit.ftsrg.contractmanager.contract.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class Status {
  @SerialName("pending")
  PENDING
}