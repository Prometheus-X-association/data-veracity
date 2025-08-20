@file:OptIn(ExperimentalUuidApi::class)

package hu.bme.mit.ftsrg.dva.api.db

import hu.bme.mit.ftsrg.dva.log.DVAVerificationRequestLog
import kotlinx.datetime.TimeZone.Companion.UTC
import kotlinx.datetime.toInstant
import kotlinx.serialization.json.Json
import org.jetbrains.exposed.v1.core.dao.id.EntityID
import org.jetbrains.exposed.v1.core.dao.id.UUIDTable
import org.jetbrains.exposed.v1.dao.UUIDEntity
import org.jetbrains.exposed.v1.dao.UUIDEntityClass
import org.jetbrains.exposed.v1.datetime.datetime
import java.net.URI
import java.util.*
import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.toKotlinUuid

object DVAVerificationRequestLogTable : UUIDTable("verification_request_logs") {
    val exchangeID = varchar("exchange_id", 255)
    val contractID = varchar("contract_id", 255)
    val attesterAgentURL = varchar("attester_agent_url", 255)
    val attesterAgentLabel = varchar("attester_agent_label", 255)
    val receivedDate = datetime("received_date")
    val verificationDate = datetime("verification_date").nullable()
    val verified = bool("verified")
    val presentationRequestData = text("presentation_request_data")
}

class DVAVerificationRequestLogEntity(id: EntityID<UUID>) : UUIDEntity(id) {
    companion object : UUIDEntityClass<DVAVerificationRequestLogEntity>(DVAVerificationRequestLogTable)

    var exchangeID by DVAVerificationRequestLogTable.exchangeID
    var contractID by DVAVerificationRequestLogTable.contractID
    var attesterAgentURL by DVAVerificationRequestLogTable.attesterAgentURL
    var attesterAgentLabel by DVAVerificationRequestLogTable.attesterAgentLabel
    var receivedDate by DVAVerificationRequestLogTable.receivedDate
    var verificationDate by DVAVerificationRequestLogTable.verificationDate
    var verified by DVAVerificationRequestLogTable.verified
    var presentationRequestData by DVAVerificationRequestLogTable.presentationRequestData
}

@OptIn(ExperimentalTime::class)
fun DVAVerificationRequestLogEntity.toModel() = DVAVerificationRequestLog(
    id = id.value.toKotlinUuid(),
    exchangeID = exchangeID,
    contractID = contractID,
    attesterAgentURL = URI(attesterAgentURL).toURL(),
    attesterAgentLabel = attesterAgentLabel,
    receivedDate = receivedDate.toInstant(UTC),
    verificationDate = verificationDate?.toInstant(UTC),
    verified = verified,
    presentationRequestData = Json.decodeFromString(presentationRequestData),
)