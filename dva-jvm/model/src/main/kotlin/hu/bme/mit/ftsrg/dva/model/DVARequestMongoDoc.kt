package hu.bme.mit.ftsrg.dva.model

import kotlinx.datetime.Instant
import kotlinx.serialization.Serializable

@Serializable
data class DVARequestMongoDoc(
  val type: String,
  val requestID: String?,
  val vlaID: String,
  val data: ByteArray,
  val attesterID: String,
  val evaluationPassing: Boolean? = null,
  val evaluationResults: String? = null,
  val receivedDate: Instant,
  val evaluationDate: Instant? = null,
  val vcIssuedDate: Instant? = null,
  val vcID: String? = null,
)