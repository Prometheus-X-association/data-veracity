package hu.bme.mit.ftsrg.odcs.model.schema

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class LogicalType {

  @SerialName("string")
  STRING,

  @SerialName("date")
  DATE,

  @SerialName("number")
  NUMBER,

  @SerialName("integer")
  INTEGER,

  @SerialName("object")
  OBJECT,

  @SerialName("array")
  ARRAY,

  @SerialName("boolean")
  BOOLEAN
}