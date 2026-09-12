@file:OptIn(ExperimentalUuidApi::class)

package hu.bme.mit.ftsrg.dva.api.db

import hu.bme.mit.ftsrg.dva.log.RequestLog
import hu.bme.mit.ftsrg.dva.log.RequestType
import kotlinx.datetime.TimeZone.Companion.UTC
import kotlinx.datetime.toInstant
import kotlinx.serialization.json.Json
import org.jetbrains.exposed.v1.core.dao.id.EntityID
import org.jetbrains.exposed.v1.core.dao.id.UUIDTable
import org.jetbrains.exposed.v1.dao.UUIDEntity
import org.jetbrains.exposed.v1.dao.UUIDEntityClass
import org.jetbrains.exposed.v1.datetime.datetime
import java.util.*
import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid
import kotlin.uuid.toKotlinUuid

object RequestLogsTable : UUIDTable("request_logs") {
    val type = varchar("type", 255)
    val exchangeID = varchar("exchange_id", 255)
    val contractID = varchar("contract_id", 255)
    val vlaID = varchar("vla_id", 255)
    val data = text("data")
    val evaluationPassing = bool("evaluation_passing")
    val evaluationResults = text("evaluation_results")
    val receivedDate = datetime("received_date")
    val vcID = varchar("vc_id", 255).nullable()
    val error = text("error").nullable()
}

class RequestLogEntity(id: EntityID<UUID>) : UUIDEntity(id) {
    companion object : UUIDEntityClass<RequestLogEntity>(RequestLogsTable)

    var type by RequestLogsTable.type
    var exchangeID by RequestLogsTable.exchangeID
    var contractID by RequestLogsTable.contractID
    var vlaID by RequestLogsTable.vlaID
    var data by RequestLogsTable.data
    var evaluationPassing by RequestLogsTable.evaluationPassing
    var evaluationResults by RequestLogsTable.evaluationResults
    var receivedDate by RequestLogsTable.receivedDate
    var vcID by RequestLogsTable.vcID
    var error by RequestLogsTable.error
}

@OptIn(ExperimentalTime::class)
fun RequestLogEntity.toModel() = RequestLog(
    id = id.value.toKotlinUuid(),
    type = RequestType.valueOf(type),
    exchangeID = Uuid.parse(exchangeID),
    contractID = Uuid.parse(contractID),
    vlaID = Uuid.parse(vlaID),
    data = Json.decodeFromString(data),
    evaluationPassing = evaluationPassing,
    evaluationResults = Json.decodeFromString(evaluationResults),
    receivedDate = receivedDate.toInstant(UTC),
    vcID = vcID?.let { Uuid.parse(it) },
    error = error?.let { Json.decodeFromString(it) },
)