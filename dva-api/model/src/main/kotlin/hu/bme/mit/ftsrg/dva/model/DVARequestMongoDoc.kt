package hu.bme.mit.ftsrg.dva.model

import kotlinx.datetime.Instant
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement

@Serializable
data class DVARequestMongoDoc(
  val type: String,
  val requestID: String?,
  val exchangeID: String,
  val contractID: String,
  val vlaID: String,
  val data: JsonElement,
  val attesterID: String,
  val evaluationPassing: Boolean? = null,
  val evaluationResults: String? = null,
  val receivedDate: Instant,
  val evaluationDate: Instant? = null,
  val vcIssuedDate: Instant? = null,
  val vcID: String? = null,
)