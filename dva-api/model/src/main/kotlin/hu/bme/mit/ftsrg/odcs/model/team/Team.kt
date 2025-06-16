@file:UseSerializers(ZonedDateTimeSerializer::class)

package hu.bme.mit.ftsrg.odcs.model.team

import hu.bme.mit.ftsrg.serialization.java.ZonedDateTimeSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import java.time.ZonedDateTime

@Serializable
data class Team(
  val username: String?,
  val role: String?,
  val dateIn: ZonedDateTime?,
  val dateOut: ZonedDateTime?,
  val replacedByUsername: String?,
)
