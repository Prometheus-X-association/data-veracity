package hu.bme.mit.ftsrg.dva.log

import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class, ExperimentalTime::class)
class FakeRequestLogRepo : RequestLogRepo {
    private val requests = mutableMapOf<Uuid, RequestLog>()

    override suspend fun all(): List<RequestLog> = requests.values.toList()

    override suspend fun byID(id: Uuid): RequestLog? = requests[id]

    override suspend fun add(request: RequestLog): RequestLog {
        requests[request.id] = request
        return request
    }
}