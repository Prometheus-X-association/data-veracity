@file:OptIn(ExperimentalUuidApi::class)

package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.err.MissingVLAErr
import hu.bme.mit.ftsrg.dva.api.err.toRequestLogError
import hu.bme.mit.ftsrg.dva.api.resource.Attestations
import hu.bme.mit.ftsrg.dva.api.upstream.Endpoint
import hu.bme.mit.ftsrg.dva.api.upstream.Upstream
import hu.bme.mit.ftsrg.dva.api.upstream.UpstreamClient
import hu.bme.mit.ftsrg.dva.api.upstream.UpstreamErr
import hu.bme.mit.ftsrg.dva.api.util.hash
import hu.bme.mit.ftsrg.dva.dto.api.AttestationRequest
import hu.bme.mit.ftsrg.dva.dto.api.AttestationResponse
import hu.bme.mit.ftsrg.dva.dto.api.AttestationVerificationRequest
import hu.bme.mit.ftsrg.dva.dto.api.AttestationVerificationResponse
import hu.bme.mit.ftsrg.dva.dto.processing.EvaluateBatchRequest
import hu.bme.mit.ftsrg.dva.dto.processing.EvaluationResult
import hu.bme.mit.ftsrg.dva.dto.vcmanager.AoVIssueRequest
import hu.bme.mit.ftsrg.dva.dto.vcmanager.AoVIssueResponse
import hu.bme.mit.ftsrg.dva.dto.vcmanager.AoVVerificationRequest
import hu.bme.mit.ftsrg.dva.dto.vcmanager.AoVVerificationResponse
import hu.bme.mit.ftsrg.dva.log.RequestLog
import hu.bme.mit.ftsrg.dva.log.RequestLogRepo
import hu.bme.mit.ftsrg.dva.log.RequestType
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.http.HttpStatusCode.Companion.OK
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.resources.post
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.json.JsonObject
import org.koin.ktor.ext.inject
import kotlin.time.Clock
import kotlin.time.ExperimentalTime
import kotlin.time.Instant
import kotlin.uuid.ExperimentalUuidApi

@OptIn(ExperimentalTime::class, ExperimentalUuidApi::class)
fun Application.aovRoutes() {
    val reqsRepo by inject<RequestLogRepo>()
    val upstreams by inject<UpstreamClient>()
    val clock by inject<Clock>()

    routing {
        post<Attestations> {
            val request: AttestationRequest = call.receive()
            val now: Instant = clock.now()

            var log = RequestLog(
                type = RequestType.ATTESTATION_REQUEST,
                exchangeID = request.exchangeID,
                contractID = request.contractID,
                vlaID = request.vlaID,
                data = request.data,
                evaluationPassing = false,
                evaluationResults = emptyList(),
                receivedDate = now,
                vcID = null
            )

            try {
                // TODO: More type safety than just JsonObject?
                val vla: JsonObject = upstreams.call(
                    endpoint = Endpoint.vla(request.vlaID),
                    mapStatus = { if (it == HttpStatusCode.NotFound) MissingVLAErr(request.vlaID) else null }
                )

                val results: List<EvaluationResult> = upstreams.call(
                    endpoint = Endpoint.EVALUATE_BATCH,
                    method = HttpMethod.Post,
                ) {
                    setBody(EvaluateBatchRequest(vla = vla, data = request.data))
                }
                if (results.isEmpty()) {
                    throw UpstreamErr.UnexpectedBody(Upstream.PROCESSING, "no evaluation results received")
                }
                val allSuccess: Boolean = results.all { it.success }
                log = log.copy(evaluationPassing = allSuccess, evaluationResults = results)

                // TODO: Is it correct to only create VC when every check passes?
                val vcIssueResult: AoVIssueResponse? = if (allSuccess) {
                    upstreams.call(
                        endpoint = Endpoint.AOV_ISSUE,
                        method = HttpMethod.Post,
                    ) {
                        setBody(
                            AoVIssueRequest(
                                // TODO: Determine what the subject should be
                                subject = hash(request.data),
                                contractId = request.contractID,
                                dataExchangeId = request.exchangeID,
                                evaluationResults = results,
                            )
                        )
                    }
                } else null
                log = log.copy(vcID = vcIssueResult?.vcID)

                call.respond<AttestationResponse>(
                    OK,
                    AttestationResponse(
                        jws = vcIssueResult?.jws,
                        evaluationPassing = allSuccess,
                        evaluationResults = results,
                    )
                )
            } catch (e: Throwable) {
                log = log.copy(error = e.toRequestLogError())
                throw e
            } finally {
                reqsRepo.add(log)
            }
        }

        post<Attestations.Verify> {
            val request: AttestationVerificationRequest = call.receive()
            val vcVerifyResult: AoVVerificationResponse = upstreams.call(
                endpoint = Endpoint.AOV_VERIFY,
                method = HttpMethod.Post
            ) {
                setBody<AoVVerificationRequest>(request)
            }

            // TODO: Log request

            call.respond<AttestationVerificationResponse>(status = OK, message = vcVerifyResult)
        }
    }
}