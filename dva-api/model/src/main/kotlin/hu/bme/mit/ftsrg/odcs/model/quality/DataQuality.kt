package hu.bme.mit.ftsrg.odcs.model.quality

import hu.bme.mit.ftsrg.odcs.model.other.AuthoritativeDefinition
import hu.bme.mit.ftsrg.odcs.model.other.CustomProperty
import kotlinx.serialization.Serializable

@Serializable
data class DataQuality(
  override val authoritativeDefinitions: List<AuthoritativeDefinition>? = null,
  override val businessImpact: String? = null,
  override val customProperties: List<CustomProperty>? = null,
  override val description: String? = null,
  override val dimension: Dimension? = null,
  override val method: String? = null,
  override val name: String? = null,
  override val schedule: String? = null,
  override val scheduler: String? = null,
  override val severity: String? = null,
  override val tags: List<String>? = null,
  override val type: DataQualityType,
  override val unit: String? = null
) : IDataQuality

