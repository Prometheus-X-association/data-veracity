package hu.bme.mit.ftsrg.dva.api.db

import hu.bme.mit.ftsrg.dva.log.VerifRequestLog
import hu.bme.mit.ftsrg.dva.log.VerifRequestLogNew
import hu.bme.mit.ftsrg.dva.log.VerifRequestLogPatch
import hu.bme.mit.ftsrg.dva.log.VerifRequestLogRepo
import kotlinx.datetime.TimeZone.Companion.UTC
import kotlinx.datetime.toLocalDateTime
import kotlinx.serialization.json.Json
import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid
import kotlin.uuid.toJavaUuid

@OptIn(ExperimentalUuidApi::class, ExperimentalTime::class)
class PgVerifRequestLogRepo : VerifRequestLogRepo {
    override suspend fun allRequests(): List<VerifRequestLog> = suspendTransaction {
        VerifRequestLogEntity.all().map { it.toModel() }
    }

    override suspend fun requestByID(id: Uuid): VerifRequestLog? = suspendTransaction {
        VerifRequestLogEntity.findById(id.toJavaUuid())?.toModel()
    }

    override suspend fun addRequest(request: VerifRequestLogNew): VerifRequestLog? =
        suspendTransaction {
            VerifRequestLogEntity.new {
                exchangeID = request.exchangeID
                contractID = request.contractID
                attesterAgentURL = request.attesterAgentURL.toURI().toURL().toString()
                attesterAgentLabel = request.attesterAgentLabel
                receivedDate = request.receivedDate.toLocalDateTime(UTC)
            }.toModel()
        }

    override suspend fun updateRequest(patch: VerifRequestLogPatch): VerifRequestLog? =
        suspendTransaction {
            VerifRequestLogEntity.findByIdAndUpdate(patch.id.toJavaUuid()) {
                it.verificationDate = patch.verificationDate?.toLocalDateTime(UTC) ?: it.verificationDate
                it.verified = patch.verified ?: it.verified
                it.presentationRequestData =
                    patch.presentationRequestData?.let { Json.encodeToString(patch.presentationRequestData) }
                        ?: it.presentationRequestData
            }?.toModel()
        }
}