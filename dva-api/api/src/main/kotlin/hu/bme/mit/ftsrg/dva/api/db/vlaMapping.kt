package hu.bme.mit.ftsrg.dva.api.db

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import org.jetbrains.exposed.v1.core.dao.id.EntityID
import org.jetbrains.exposed.v1.core.dao.id.UUIDTable
import org.jetbrains.exposed.v1.dao.UUIDEntity
import org.jetbrains.exposed.v1.dao.UUIDEntityClass
import java.util.*

object VLAsTable : UUIDTable("vlas") {
    val odcs = text("odcs_json")
}

class VLAEntity(id: EntityID<UUID>) : UUIDEntity(id) {
    companion object : UUIDEntityClass<VLAEntity>(VLAsTable)

    var odcs by VLAsTable.odcs
}

fun VLAEntity.toModel() = Json.decodeFromString<JsonObject>(odcs)