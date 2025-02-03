@file:UseSerializers(ZonedDateTimeSerializer::class)

package hu.bme.mit.ftsrg.odcs.model


import hu.bme.mit.ftsrg.odcs.model.fundamentals.APIVersion
import hu.bme.mit.ftsrg.odcs.model.fundamentals.Description
import hu.bme.mit.ftsrg.odcs.model.fundamentals.FileKind
import hu.bme.mit.ftsrg.odcs.model.other.AuthoritativeDefinition
import hu.bme.mit.ftsrg.odcs.model.pricing.Pricing
import hu.bme.mit.ftsrg.odcs.model.roles.Role
import hu.bme.mit.ftsrg.odcs.model.schema.SchemaObject
import hu.bme.mit.ftsrg.odcs.model.servers.Server
import hu.bme.mit.ftsrg.odcs.model.sla.SLAProperty
import hu.bme.mit.ftsrg.odcs.model.support.SupportItem
import hu.bme.mit.ftsrg.odcs.model.team.Team
import hu.bme.mit.ftsrg.serialization.java.ZonedDateTimeSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import java.time.ZonedDateTime

@Serializable
data class Contract(
  val apiVersion: APIVersion,
  val authoritativeDefinitions: List<AuthoritativeDefinition>? = null,
  val contractCreatedTs: ZonedDateTime? = null,
  val dataProduct: String? = null,
  val description: Description? = null,
  val domain: String? = null,
  val id: String,
  val kind: FileKind,
  val name: String? = null,
  val price: Pricing? = null,
  val roles: List<Role>? = null,
  val schema: List<SchemaObject>,
  val servers: List<Server>? = null,
  val slaDefaultElement: String? = null,
  val slaProperties: List<SLAProperty>? = null,
  val status: String,
  val support: List<SupportItem>? = null,
  val tags: List<String>? = null,
  val team: List<Team>? = null,
  val tenant: String? = null,
  val version: String,
)
