package hu.bme.mit.ftsrg.connector.model

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject

@Serializable
data class DataExchange(
  val contract: String,
  val purposeId: String,
  val resourceId: String,
  val dataProcessingId: String,
  val targetId: String,
  val data: JsonObject
)
