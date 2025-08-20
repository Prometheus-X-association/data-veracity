package hu.bme.mit.ftsrg.dva.log

import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class, ExperimentalTime::class)
class FakeDVARequestLogRepository : DVARequestLogRepository {
    private val requests = mutableMapOf<Uuid, DVARequestLog>()

    override suspend fun allRequests(): List<DVARequestLog> = requests.values.toList()

    override suspend fun requestByID(id: Uuid): DVARequestLog? = requests[id]

    override suspend fun addRequest(request: NewDVARequestLog): DVARequestLog? {
        val entity = DVARequestLog(
            id = Uuid.random(),
            type = request.type,
            requestID = request.requestID,
            exchangeID = request.exchangeID,
            contractID = request.contractID,
            vlaID = request.vlaID,
            data = request.data,
            attesterID = request.attesterID,
            evaluationPassing = request.evaluationPassing,
            evaluationResults = request.evaluationResults,
            receivedDate = request.receivedDate,
            evaluationDate = request.evaluationDate,
            vcIssuedDate = request.vcIssuedDate,
            vcID = request.vcID,
        )
        requests.put(entity.id, entity)
        return entity
    }
}