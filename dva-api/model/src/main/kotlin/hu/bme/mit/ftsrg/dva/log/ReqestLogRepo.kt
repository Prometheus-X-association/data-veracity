package hu.bme.mit.ftsrg.dva.log

import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class)
interface ReqestLogRepo {
    suspend fun allRequests(): List<RequestLog>
    suspend fun requestByID(id: Uuid): RequestLog?
    suspend fun addRequest(request: RequestLogNew): RequestLog?
}