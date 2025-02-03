package hu.bme.mit.ftsrg.odcs.model.quality

import kotlinx.serialization.Contextual
import kotlinx.serialization.Serializable

@Serializable
data class DataQualityLibrary(
  val dataQuality: IDataQuality,
  val mustBe: @Contextual Any?,
  val mustBeBetween: Pair<@Contextual Number, @Contextual Number>?,
  val mustBeGreaterOrEqualTo: @Contextual Number?,
  val mustBeGreaterThan: @Contextual Number?,
  val mustBeLessOrEqualTo: @Contextual Number?,
  val mustBeLessThan: @Contextual Number?,
  val mustNotBe: String?,
  val mustNotBeBetween: Pair<@Contextual Number, @Contextual Number>?,
  val rule: String,
) : IDataQuality by dataQuality
