package hu.bme.mit.ftsrg.odcs.model.quality

import kotlinx.serialization.Serializable

@Serializable
data class DataQualityCustom(
  val engine: String,
  val implementation: String,
  val dataQuality: IDataQuality,
) : IDataQuality by dataQuality