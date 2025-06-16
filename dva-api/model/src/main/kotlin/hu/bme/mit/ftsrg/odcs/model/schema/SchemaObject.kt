package hu.bme.mit.ftsrg.odcs.model.schema

import hu.bme.mit.ftsrg.odcs.model.quality.IDataQuality
import kotlinx.serialization.Serializable

@Serializable
data class SchemaObject(
  val logicalType: LogicalType,
  val dataGranularityDescription: String? = null,
  val properties: List<SchemaProperty>,
  val physicalName: String? = null,
  val quality: List<IDataQuality>? = null,
  val schemaElement: ISchemaElement,
) : ISchemaElement by schemaElement