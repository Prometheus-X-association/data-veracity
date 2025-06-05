@file:UseSerializers(URLSerializer::class)

package hu.bme.mit.ftsrg.dva.dto.aov

import hu.bme.mit.ftsrg.contractmanager.contract.model.Contract
import hu.bme.mit.ftsrg.serialization.java.URLSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import java.net.URL
import org.bson.types.ObjectId
import org.bson.codecs.pojo.annotations.BsonId
import kotlinx.datetime.Clock
import kotlinx.datetime.Instant

@Serializable
data class AttestationRequestDTO(
  val id: String? = null,
  val contract: Contract,
  val data: ByteArray,
  val attesterID: String,
  val callbackURL: URL,
  val mapping: Map<String, String>,
)

@Serializable
data class AttestationRequestDTOMongo(
  val id: String?,
  val vlaId: String,
  val data: ByteArray,
  val attesterID: String,
  val callbackURL: String,
  val mapping: Map<String, String>,
  val successful: Boolean? = null,
  val date: Instant = Clock.System.now(),
)