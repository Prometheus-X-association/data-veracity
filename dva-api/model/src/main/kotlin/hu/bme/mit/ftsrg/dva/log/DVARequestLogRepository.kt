package hu.bme.mit.ftsrg.dva.log

import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class)
interface DVARequestLogRepository {
    suspend fun allRequests(): List<DVARequestLog>
    suspend fun requestByID(id: Uuid): DVARequestLog?
    suspend fun addRequest(request: NewDVARequestLog): DVARequestLog?
}