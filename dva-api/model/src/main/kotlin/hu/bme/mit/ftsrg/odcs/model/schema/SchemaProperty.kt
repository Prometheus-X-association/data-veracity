package hu.bme.mit.ftsrg.odcs.model.schema

import hu.bme.mit.ftsrg.odcs.model.quality.IDataQuality
import kotlinx.serialization.Contextual
import kotlinx.serialization.Serializable

@Serializable
data class SchemaProperty(
  val primaryKey: Boolean = false,
  val primaryKeyPosition: Int = -1,
  val logicalType: LogicalType,
  val logicalTypeOptions: Map<String, String>? = null,
  val required: Boolean = false,
  val unique: Boolean = false,
  val partitioned: Boolean = false,
  val partitionKeyPosition: Int = -1,
  val classification: String? = null,
  val encryptedName: String? = null,
  val transformSourceObjects: List<String>? = null,
  val transformLogic: String? = null,
  val transformDescription: String? = null,
  val examples: List<@Contextual Any>? = null,
  val criticalDataElement: Boolean = false,
  val quality: List<IDataQuality>? = null,
  val schemaElement: ISchemaElement,
) : ISchemaElement by schemaElement
