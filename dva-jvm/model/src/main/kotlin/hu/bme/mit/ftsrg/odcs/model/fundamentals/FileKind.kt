package hu.bme.mit.ftsrg.odcs.model.fundamentals

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class FileKind {

  @SerialName("DataContract")
  DATA_CONTRACT
}