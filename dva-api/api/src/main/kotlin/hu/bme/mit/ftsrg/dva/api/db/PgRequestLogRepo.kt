package hu.bme.mit.ftsrg.dva.api.db

import hu.bme.mit.ftsrg.dva.log.RequestLog
import hu.bme.mit.ftsrg.dva.log.RequestLogRepo
import kotlinx.datetime.TimeZone.Companion.UTC
import kotlinx.datetime.toLocalDateTime
import kotlinx.serialization.json.Json
import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid
import kotlin.uuid.toJavaUuid

@OptIn(ExperimentalUuidApi::class, ExperimentalTime::class)
class PgRequestLogRepo : RequestLogRepo {
    override suspend fun all(): List<RequestLog> = suspendTransaction {
        RequestLogEntity.all().map { it.toModel() }
    }

    override suspend fun byID(id: Uuid): RequestLog? = suspendTransaction {
        RequestLogEntity.findById(id.toJavaUuid())?.toModel()
    }

    override suspend fun add(request: RequestLog): RequestLog? = suspendTransaction {
        RequestLogEntity.new {
            type = request.type.name
            exchangeID = request.exchangeID.toString()
            contractID = request.contractID.toString()
            vlaID = request.vlaID.toString()
            data = Json.encodeToString(request.data)
            evaluationPassing = request.evaluationPassing
            evaluationResults = Json.encodeToString(request.evaluationResults)
            receivedDate = request.receivedDate.toLocalDateTime(UTC)
            vcID = request.vcID.toString()
            error = request.error?.let { Json.encodeToString(it) }
        }.toModel()
    }
}