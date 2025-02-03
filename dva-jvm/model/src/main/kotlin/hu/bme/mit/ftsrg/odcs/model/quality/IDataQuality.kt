package hu.bme.mit.ftsrg.odcs.model.quality

import hu.bme.mit.ftsrg.odcs.model.other.AuthoritativeDefinition
import hu.bme.mit.ftsrg.odcs.model.other.CustomProperty
import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonClassDiscriminator

@OptIn(ExperimentalSerializationApi::class)
@Serializable
@JsonClassDiscriminator("data_quality_type")
sealed interface IDataQuality {
  val authoritativeDefinitions: List<AuthoritativeDefinition>?
  val businessImpact: String?
  val customProperties: List<CustomProperty>?
  val description: String?
  val dimension: Dimension?
  val method: String?
  val name: String?
  val schedule: String?
  val scheduler: String?
  val severity: String?
  val tags: List<String>?
  val type: DataQualityType
  val unit: String?
}