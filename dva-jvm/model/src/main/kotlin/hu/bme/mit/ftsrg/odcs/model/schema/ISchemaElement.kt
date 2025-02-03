package hu.bme.mit.ftsrg.odcs.model.schema

import hu.bme.mit.ftsrg.odcs.model.other.AuthoritativeDefinition
import hu.bme.mit.ftsrg.odcs.model.other.CustomProperty
import kotlinx.serialization.Serializable

@Serializable
sealed interface ISchemaElement {
  val authoritativeDefinitions: List<AuthoritativeDefinition>?
  val businessName: String?
  val customProperties: List<CustomProperty>?
  val description: String?
  val name: String
  val physicalType: String?
  val tags: List<String>?
}