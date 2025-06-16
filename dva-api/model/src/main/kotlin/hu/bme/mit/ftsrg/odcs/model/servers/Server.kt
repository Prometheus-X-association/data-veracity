package hu.bme.mit.ftsrg.odcs.model.servers

import hu.bme.mit.ftsrg.odcs.model.other.CustomProperty
import hu.bme.mit.ftsrg.odcs.model.roles.Role
import kotlinx.serialization.Serializable

@Serializable
data class Server(
  val server: String,
  val type: ServerType,
  val description: String?,
  val environment: String?,
  val roles: List<Role>?,
  val customProperties: List<CustomProperty>?,
)
