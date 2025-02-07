package hu.bme.mit.ftsrg.odcs.model.fundamentals

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class APIVersion {

  @SerialName("v3.0.1")
  V3_0_1,

  @SerialName("v3.0.0")
  V3_0_0,

  @SerialName("v2.2.2")
  V2_2_2,

  @SerialName("v2.2.1")
  V2_2_1,

  @SerialName("v2.2.0")
  V2_2_0,
}