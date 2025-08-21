package hu.bme.mit.ftsrg.dva.log

import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class)
interface VerifRequestLogRepo {
    suspend fun allRequests(): List<VerifRequestLog>
    suspend fun requestByID(id: Uuid): VerifRequestLog?
    suspend fun addRequest(request: VerifRequestLogNew): VerifRequestLog?
    suspend fun updateRequest(patch: VerifRequestLogPatch): VerifRequestLog?
}