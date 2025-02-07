package hu.bme.mit.ftsrg.odcs.model.schema

import hu.bme.mit.ftsrg.odcs.model.other.AuthoritativeDefinition
import hu.bme.mit.ftsrg.odcs.model.other.CustomProperty
import kotlinx.serialization.Serializable

@Serializable
data class SchemaElement(
  override val authoritativeDefinitions: List<AuthoritativeDefinition>? = null,
  override val businessName: String? = null,
  override val customProperties: List<CustomProperty>? = null,
  override val description: String? = null,
  override val name: String,
  override val physicalType: String? = null,
  override val tags: List<String>? = null
) : ISchemaElement
