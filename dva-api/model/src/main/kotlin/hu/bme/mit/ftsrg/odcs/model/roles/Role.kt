package hu.bme.mit.ftsrg.odcs.model.roles

import hu.bme.mit.ftsrg.odcs.model.other.CustomProperty
import kotlinx.serialization.Serializable

@Serializable
data class Role(
  val access: String?,
  val customProperties: List<CustomProperty>?,
  val description: String?,
  val firstLevelApprovers: String?,
  val role: String,
  val secondLevelApprovers: String?,
)
