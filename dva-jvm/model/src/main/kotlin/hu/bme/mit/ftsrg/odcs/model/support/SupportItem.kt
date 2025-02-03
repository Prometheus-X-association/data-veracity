@file:UseSerializers(URLSerializer::class)

package hu.bme.mit.ftsrg.odcs.model.support

import hu.bme.mit.ftsrg.serialization.java.URLSerializer
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import java.net.URL

@Serializable
data class SupportItem(
  val channel: String,
  val url: URL,
  val description: String?,
  val tool: String?,
  val scope: String?,
  @SerialName("invitationUrl") val invitationURL: URL?,
)
