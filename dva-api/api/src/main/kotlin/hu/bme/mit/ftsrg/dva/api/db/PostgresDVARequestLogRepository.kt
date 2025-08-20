package hu.bme.mit.ftsrg.dva.api.db

import hu.bme.mit.ftsrg.dva.log.DVARequestLog
import hu.bme.mit.ftsrg.dva.log.DVARequestLogRepository
import hu.bme.mit.ftsrg.dva.log.NewDVARequestLog
import kotlinx.datetime.TimeZone.Companion.UTC
import kotlinx.datetime.toLocalDateTime
import kotlinx.serialization.json.Json
import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid
import kotlin.uuid.toJavaUuid

@OptIn(ExperimentalUuidApi::class, ExperimentalTime::class)
class PostgresDVARequestLogRepository : DVARequestLogRepository {
    override suspend fun allRequests(): List<DVARequestLog> = suspendTransaction {
        DVARequestLogEntity.all().map { it.toModel() }
    }

    override suspend fun requestByID(id: Uuid): DVARequestLog? = suspendTransaction {
        DVARequestLogEntity.findById(id.toJavaUuid())?.toModel()
    }

    override suspend fun addRequest(request: NewDVARequestLog): DVARequestLog? = suspendTransaction {
        DVARequestLogEntity.new {
            type = request.type.name
            requestID = request.requestID.toString()
            exchangeID = request.exchangeID
            contractID = request.contractID
            vlaID = request.vlaID.toString()
            data = Json.encodeToString(request.data)
            attesterID = request.attesterID
            evaluationPassing = request.evaluationPassing ?: false
            evaluationResults = Json.encodeToString(request.evaluationResults)
            receivedDate = request.receivedDate.toLocalDateTime(UTC)
            evaluationDate = request.evaluationDate?.toLocalDateTime(UTC)
            vcIssuedDate = request.vcIssuedDate?.toLocalDateTime(UTC)
            vcID = request.vcID
        }.toModel()
    }
}