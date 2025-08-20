@file:OptIn(ExperimentalUuidApi::class)

package hu.bme.mit.ftsrg.dva.api.db

import hu.bme.mit.ftsrg.dva.log.DVARequestLog
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

object DVARequestLogTable : UUIDTable("request_logs") {
    val type = varchar("type", 255)
    val requestID = varchar("request_id", 255)
    val exchangeID = varchar("exchange_id", 255)
    val contractID = varchar("contract_id", 255)
    val vlaID = varchar("vla_id", 255)
    val data = text("data")
    val attesterID = varchar("attester_id", 255)
    val evaluationPassing = bool("evaluation_passing").nullable()
    val evaluationResults = text("evaluation_results").nullable()
    val receivedDate = datetime("received_date")
    val evaluationDate = datetime("evaluation_date").nullable()
    val vcIssuedDate = datetime("vc_issued_date").nullable()
    val vcID = varchar("vc_id", 255).nullable()
}

class DVARequestLogEntity(id: EntityID<UUID>) : UUIDEntity(id) {
    companion object : UUIDEntityClass<DVARequestLogEntity>(DVARequestLogTable)

    var type by DVARequestLogTable.type
    var requestID by DVARequestLogTable.requestID
    var exchangeID by DVARequestLogTable.exchangeID
    var contractID by DVARequestLogTable.contractID
    var vlaID by DVARequestLogTable.vlaID
    var data by DVARequestLogTable.data
    var attesterID by DVARequestLogTable.attesterID
    var evaluationPassing by DVARequestLogTable.evaluationPassing
    var evaluationResults by DVARequestLogTable.evaluationResults
    var receivedDate by DVARequestLogTable.receivedDate
    var evaluationDate by DVARequestLogTable.evaluationDate
    var vcIssuedDate by DVARequestLogTable.vcIssuedDate
    var vcID by DVARequestLogTable.vcID
}

@OptIn(ExperimentalTime::class)
fun DVARequestLogEntity.toModel() = DVARequestLog(
    id = id.value.toKotlinUuid(),
    type = RequestType.valueOf(type),
    requestID = Uuid.parse(requestID),
    exchangeID = exchangeID,
    contractID = contractID,
    vlaID = Uuid.parse(vlaID),
    data = Json.decodeFromString(data),
    attesterID = attesterID,
    evaluationPassing = evaluationPassing,
    evaluationResults = evaluationResults,
    receivedDate = receivedDate.toInstant(UTC),
    evaluationDate = evaluationDate?.toInstant(UTC),
    vcIssuedDate = vcIssuedDate?.toInstant(UTC),
    vcID = vcID,
)