package hu.bme.mit.ftsrg.odcs.model.quality

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class Dimension {

  @SerialName("accuracy")
  ACCURACY,

  @SerialName("completeness")
  COMPLETENESS,

  @SerialName("conformity")
  CONFORMITY,

  @SerialName("consistency")
  CONSISTENCY,

  @SerialName("coverage")
  COVERAGE,

  @SerialName("timeliness")
  TIMELINESS,

  @SerialName("uniqueness")
  UNIQUENESS
}
