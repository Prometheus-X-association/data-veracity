package hu.bme.mit.ftsrg.odcs.model.quality

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class DataQualityType {

  @SerialName("text")
  TEXT,

  @SerialName("library")
  LIBRARY,

  @SerialName("sql")
  SQL,

  @SerialName("custom")
  CUSTOM
}