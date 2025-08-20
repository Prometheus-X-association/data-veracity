package hu.bme.mit.ftsrg.dva.log

import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class)
interface DVAVerificationRequestLogRepository {
    suspend fun allRequests(): List<DVAVerificationRequestLog>
    suspend fun requestByID(id: Uuid): DVAVerificationRequestLog?
    suspend fun addRequest(request: NewDVAVerificationRequestLog): DVAVerificationRequestLog?
    suspend fun updateRequest(patch: DVAVerificationRequestLogPatch): DVAVerificationRequestLog?
}