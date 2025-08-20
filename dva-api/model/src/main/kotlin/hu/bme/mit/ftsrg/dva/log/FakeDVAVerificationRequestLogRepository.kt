package hu.bme.mit.ftsrg.dva.log

import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class, ExperimentalTime::class)
class FakeDVAVerificationRequestLogRepository : DVAVerificationRequestLogRepository {
    private val requests = mutableMapOf<Uuid, DVAVerificationRequestLog>()

    override suspend fun allRequests(): List<DVAVerificationRequestLog> = requests.values.toList()

    override suspend fun requestByID(id: Uuid): DVAVerificationRequestLog? = requests[id]

    override suspend fun addRequest(request: NewDVAVerificationRequestLog): DVAVerificationRequestLog? {
        val entity = DVAVerificationRequestLog(
            id = Uuid.random(),
            exchangeID = request.exchangeID,
            contractID = request.contractID,
            attesterAgentURL = request.attesterAgentURL,
            attesterAgentLabel = request.attesterAgentLabel,
            receivedDate = request.receivedDate,
        )
        requests.put(entity.id, entity)
        return entity
    }

    override suspend fun updateRequest(patch: DVAVerificationRequestLogPatch): DVAVerificationRequestLog? {
        val existingRequest = requests[patch.id] ?: return null
        val updatedRequest = DVAVerificationRequestLog(
            id = existingRequest.id,
            exchangeID = existingRequest.exchangeID,
            contractID = existingRequest.contractID,
            attesterAgentURL = existingRequest.attesterAgentURL,
            attesterAgentLabel = existingRequest.attesterAgentLabel,
            receivedDate = existingRequest.receivedDate,
            verificationDate = patch.verificationDate ?: existingRequest.verificationDate,
            verified = patch.verified ?: existingRequest.verified,
            presentationRequestData = patch.presentationRequestData ?: existingRequest.presentationRequestData,
        )
        requests.put(updatedRequest.id, updatedRequest)
        return updatedRequest
    }
}