package hu.bme.mit.ftsrg.dva.api.db

import hu.bme.mit.ftsrg.dva.log.DVAVerificationRequestLog
import hu.bme.mit.ftsrg.dva.log.DVAVerificationRequestLogPatch
import hu.bme.mit.ftsrg.dva.log.DVAVerificationRequestLogRepository
import hu.bme.mit.ftsrg.dva.log.NewDVAVerificationRequestLog
import kotlinx.datetime.TimeZone.Companion.UTC
import kotlinx.datetime.toLocalDateTime
import kotlinx.serialization.json.Json
import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid
import kotlin.uuid.toJavaUuid

@OptIn(ExperimentalUuidApi::class, ExperimentalTime::class)
class PostgresDVAVerificationRequestLogRepository : DVAVerificationRequestLogRepository {
    override suspend fun allRequests(): List<DVAVerificationRequestLog> = suspendTransaction {
        DVAVerificationRequestLogEntity.all().map { it.toModel() }
    }

    override suspend fun requestByID(id: Uuid): DVAVerificationRequestLog? = suspendTransaction {
        DVAVerificationRequestLogEntity.findById(id.toJavaUuid())?.toModel()
    }

    override suspend fun addRequest(request: NewDVAVerificationRequestLog): DVAVerificationRequestLog? =
        suspendTransaction {
            DVAVerificationRequestLogEntity.new {
                exchangeID = request.exchangeID
                contractID = request.contractID
                attesterAgentURL = request.attesterAgentURL.toURI().toURL().toString()
                attesterAgentLabel = request.attesterAgentLabel
                receivedDate = request.receivedDate.toLocalDateTime(UTC)
            }.toModel()
        }

    override suspend fun updateRequest(patch: DVAVerificationRequestLogPatch): DVAVerificationRequestLog? =
        suspendTransaction {
            DVAVerificationRequestLogEntity.findByIdAndUpdate(patch.id.toJavaUuid()) {
                it.verificationDate = patch.verificationDate?.toLocalDateTime(UTC) ?: it.verificationDate
                it.verified = patch.verified ?: it.verified
                it.presentationRequestData =
                    patch.presentationRequestData?.let { Json.encodeToString(patch.presentationRequestData) }
                        ?: it.presentationRequestData
            }?.toModel()
        }
}