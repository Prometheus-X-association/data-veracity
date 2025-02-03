package hu.bme.mit.ftsrg.odcs.model.quality

import kotlinx.serialization.Serializable

@Serializable
data class DataQualitySQL(
  val query: String,
  val dataQuality: IDataQuality,
) : IDataQuality by dataQuality
