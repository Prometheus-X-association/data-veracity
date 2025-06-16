package hu.bme.mit.ftsrg.odcs.model.fundamentals

import hu.bme.mit.ftsrg.odcs.model.other.AuthoritativeDefinition
import hu.bme.mit.ftsrg.odcs.model.other.CustomProperty
import kotlinx.serialization.Serializable

@Serializable
data class Description(
  val purpose: String?,
  val limitations: String?,
  val usage: String?,
  val authoritativeDefinitions: List<AuthoritativeDefinition>?,
  val customProperties: List<CustomProperty>?,
)
