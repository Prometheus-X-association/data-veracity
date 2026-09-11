@file:OptIn(ExperimentalTime::class, ExperimentalUuidApi::class)

package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.err.ErrType
import hu.bme.mit.ftsrg.dva.api.testutil.*
import hu.bme.mit.ftsrg.dva.api.upstream.Endpoint
import hu.bme.mit.ftsrg.dva.api.upstream.Upstream
import hu.bme.mit.ftsrg.dva.api.upstream.UpstreamClient
import hu.bme.mit.ftsrg.dva.api.upstream.configureForUpstreams
import hu.bme.mit.ftsrg.dva.api.util.hash
import hu.bme.mit.ftsrg.dva.dto.api.*
import hu.bme.mit.ftsrg.dva.dto.processing.EvaluateBatchRequest
import hu.bme.mit.ftsrg.dva.dto.processing.EvaluationResult
import hu.bme.mit.ftsrg.dva.dto.vcmanager.AoVIssueRequest
import hu.bme.mit.ftsrg.dva.dto.vcmanager.AoVIssueResponse
import hu.bme.mit.ftsrg.dva.dto.vcmanager.AoVVerificationRequest
import hu.bme.mit.ftsrg.dva.dto.vcmanager.AoVVerificationResponse
import hu.bme.mit.ftsrg.dva.log.RequestLog
import hu.bme.mit.ftsrg.dva.log.RequestLogRepo
import hu.bme.mit.ftsrg.dva.log.RequestType
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.mock.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.content.*
import io.ktor.http.*
import io.ktor.http.HttpStatusCode.Companion.BadGateway
import io.ktor.http.HttpStatusCode.Companion.NotFound
import io.ktor.http.HttpStatusCode.Companion.OK
import io.ktor.http.HttpStatusCode.Companion.UnprocessableEntity
import io.ktor.http.HttpStatusCode.Companion.UnsupportedMediaType
import io.ktor.server.application.*
import io.ktor.server.testing.*
import io.ktor.util.network.*
import io.mockk.*
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonObject
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.assertNull
import org.junit.jupiter.params.ParameterizedTest
import org.junit.jupiter.params.provider.Arguments
import org.junit.jupiter.params.provider.MethodSource
import org.koin.dsl.module
import org.koin.ktor.plugin.Koin
import java.net.ConnectException
import kotlin.time.Clock
import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

// --- Fixtures ---------------------------------------------------------------

private val xchgUUID = Uuid.random()
private val contractUUID = Uuid.random()
private val vlaUUID = Uuid.random()

private val emptyVLA = buildJsonObject {}

private val passingData = buildJsonObject { putJsonObject("result") { put("success", true) } }

private val attestationRequest = AttestationRequest(
    exchangeID = xchgUUID,
    contractID = contractUUID,
    vlaID = vlaUUID,
    data = passingData,
)

private val passingEvalResult = EvaluationResult(
    engine = "TEST_ENGINE", timestamp = FixedClock.now(), success = true
)

private val failingEvalResult = EvaluationResult(
    engine = "TEST_ENGINE",
    timestamp = FixedClock.now(),
    success = false,
    error = "test engine failed due to foo bar baz"
)

private val testJWS = "jws_placeholder"
private val successfullyIssuedAoV = AoVIssueResponse(jws = testJWS, vcID = Uuid.random())

private val successfullyVerifiedAoV = AoVVerificationResponse(verified = true)

private val expectedLog = RequestLog(
    type = RequestType.ATTESTATION_REQUEST,
    exchangeID = xchgUUID,
    contractID = contractUUID,
    vlaID = vlaUUID,
    data = passingData,
    evaluationPassing = true,
    evaluationResults = listOf(passingEvalResult),
    receivedDate = FixedClock.now(),
    vcID = successfullyIssuedAoV.vcID,
)

private val verificationRequest = AttestationVerificationRequest(jws = testJWS)

/** The upstreams the attestation route calls, in the order it calls them. */
private val callOrder = listOf(Endpoint.vla(vlaUUID), Endpoint.EVALUATE_BATCH, Endpoint.AOV_ISSUE)

// --- Arrangement ------------------------------------------------------------

private val HttpRequestData.endpointPath: String
    get() = url.encodedPath.removePrefix("/")

private suspend fun HttpClient.postAttestation(request: AttestationRequest = attestationRequest): HttpResponse =
    post("/attestation") { setBody(request) }

private suspend fun HttpClient.postVerification(request: AttestationVerificationRequest = verificationRequest): HttpResponse =
    post("/attestation/verify") { setBody(request) }

private suspend fun HttpClient.postRaw(
    path: String,
    body: String,
    contentType: ContentType = ContentType.Application.Json,
): HttpResponse = post(path) { setBody(TextContent(body, contentType)) }

private fun upstreams(
    vla: MockResponder = { jsonResponse(emptyVLA) },
    evaluate: MockResponder = { jsonResponse(listOf(passingEvalResult)) },
    issue: MockResponder = { jsonResponse(successfullyIssuedAoV) },
    verify: MockResponder = { jsonResponse(successfullyVerifiedAoV) },
): MockResponder = { req ->
    when (req.endpointPath) {
        Endpoint.vla(vlaUUID).path -> vla(req)
        Endpoint.EVALUATE_BATCH.path -> evaluate(req)
        Endpoint.AOV_ISSUE.path -> issue(req)
        Endpoint.AOV_VERIFY.path -> verify(req)
        else -> respondError(NotFound)
    }
}

private fun failingAt(endpoint: Endpoint, error: () -> Throwable): MockResponder {
    val croak: MockResponder = { throw error() }
    return when (endpoint) {
        Endpoint.EVALUATE_BATCH -> upstreams(evaluate = croak)
        Endpoint.AOV_ISSUE -> upstreams(issue = croak)
        else -> upstreams(vla = croak)
    }
}

class AoVRoutesTest {
    private val reqsRepo: RequestLogRepo = mockk()
    private val sentRequests = mutableListOf<HttpRequestData>()

    @BeforeEach
    fun setup() {
        coEvery { reqsRepo.add(any()) } answers { firstArg() }
    }

    @Test
    fun `attestation returns 200 when everything checks out`() = testApplication {
        // Arrange
        setupApplication(upstreams())
        val client = createTestClient()

        // Act
        // Assert response payload
        client.postAttestation().apply {
            assertEquals(OK, status)
            val body: AttestationResponse = body()
            assertEquals(testJWS, body.jws)
            assertTrue(body.evaluationPassing)
            assertEquals(listOf(passingEvalResult), body.evaluationResults)
        }

        // Assert upstream requests
        assertUpstreamEndpoints(Endpoint.vla(vlaUUID), Endpoint.EVALUATE_BATCH, Endpoint.AOV_ISSUE)

        // Assert upstream request bodies
        // (VLA request is just a GET to /vla/{id} so there is nothing else to assert)
        val evalRequestSent: EvaluateBatchRequest = sentBody(Endpoint.EVALUATE_BATCH)
        assertEquals(EvaluateBatchRequest(vla = emptyVLA, data = passingData), evalRequestSent)
        val vcRequestSent: AoVIssueRequest = sentBody(Endpoint.AOV_ISSUE)
        assertEquals(
            AoVIssueRequest(
                subject = hash(passingData),
                contractId = contractUUID,
                dataExchangeId = xchgUUID,
                evaluationResults = listOf(passingEvalResult)
            ), vcRequestSent
        )

        // Assert db logging
        assertLogged(expectedLog)
    }

    @Test
    fun `attestation returns 200 with null JWS when evaluations do not pass`() = testApplication {
        // Arrange
        setupApplication(upstreams(evaluate = { jsonResponse(listOf(failingEvalResult)) }))
        val client = createTestClient()

        // Act
        // Assert response payload
        client.postAttestation().apply {
            assertEquals(OK, status)
            val body: AttestationResponse = body()
            assertNull(body.jws)
            assertFalse(body.evaluationPassing)
            assertEquals(listOf(failingEvalResult), body.evaluationResults)
            assertFalse(bodyAsText().contains("jws"), "unissued JWS should be omitted, not null")
        }

        // Assert upstream requests
        assertUpstreamEndpoints(Endpoint.vla(vlaUUID), Endpoint.EVALUATE_BATCH)

        // Assert db logging
        assertLogged(
            expectedLog.copy(
                evaluationPassing = false, evaluationResults = listOf(failingEvalResult), vcID = null
            )
        )
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("attestationUpstreamTransportFailures")
    fun `attestation upstream transport failure handled`(case: String, failing: Endpoint, error: () -> Throwable) =
        testApplication {
            // Arrange
            setupApplication(failingAt(failing, error))
            val client = createTestClient()

            // Act
            // Assert response payload
            client.postAttestation().assertIsError(BadGateway, ErrType.BAD_GATEWAY)

            // Assert upstream requests
            assertUpstreamEndpoints(*callOrder.take(callOrder.indexOf(failing) + 1).toTypedArray())

            // Assert db logging
            assertErrorLogged()
        }

    @Test
    fun `attestation handles when VLA is not found`() = testApplication {
        // Arrange
        setupApplication(upstreams(vla = { respondError(NotFound) }))
        val client = createTestClient()

        // Act
        // Assert response payload
        client.postAttestation().apply {
            assertEquals(NotFound, status)
            val body: ErrDTO = body()
            assertEquals(ErrType.NOT_FOUND.uri.toString(), body.type)
            assertEquals(ErrType.NOT_FOUND.title, body.title)
        }

        // Assert upstream paths
        assertUpstreamEndpoints(Endpoint.vla(vlaUUID))

        // Assert db logging
        assertErrorLogged()
    }

    @Test
    fun `attestation handles when processing results are empty`() = testApplication {
        // Arrange
        setupApplication(upstreams(evaluate = { jsonResponse<List<EvaluationResult>>(emptyList()) }))
        val client = createTestClient()

        // Act
        // Assert response payload
        client.postAttestation().apply {
            assertEquals(BadGateway, status)
            val body: ErrDTO = body()
            assertEquals(ErrType.BAD_GATEWAY.uri.toString(), body.type)
            assertEquals(ErrType.BAD_GATEWAY.title, body.title)
        }

        // Assert upstream paths
        assertUpstreamEndpoints(Endpoint.vla(vlaUUID), Endpoint.EVALUATE_BATCH)

        // Assert db logging
        assertErrorLogged()
    }

    @Test
    fun `attestation verification returns 200 when everything checks out`() = testApplication {
        // Arrange
        setupApplication(upstreams())
        val client = createTestClient()

        // Act
        // Assert response payload
        client.postVerification().apply {
            assertEquals(OK, status)
            val body: AttestationVerificationResponse = body()
            assertTrue(body.verified)
            assertNull(body.reason)
        }

        // Assert upstream requests
        assertUpstreamEndpoints(Endpoint.AOV_VERIFY)

        // Assert upstream request bodies
        val vcRequestSent: AoVVerificationRequest = sentBody(Endpoint.AOV_VERIFY)
        assertEquals(AoVVerificationRequest(jws = testJWS), vcRequestSent)

        // TODO: assert logged
    }

    @Test
    fun `attestation verification handles VC manager unreachable`() = testApplication {
        // Arrange
        setupApplication(upstreams(verify = { throw ConnectException() }))
        val client = createTestClient()

        // Act
        // Assert response payload
        client.postVerification().apply {
            assertEquals(BadGateway, status)
            val body: ErrDTO = body()
            assertEquals(ErrType.BAD_GATEWAY.uri.toString(), body.type)
            assertEquals(ErrType.BAD_GATEWAY.title, body.title)
        }

        // Assert upstream requests
        assertUpstreamEndpoints(Endpoint.AOV_VERIFY)

        // TODO: assert logged
    }

    @Test
    fun `attestation verification handles VC manager unresolvable`() = testApplication {
        // Arrange
        setupApplication(upstreams(verify = { throw UnresolvedAddressException() }))
        val client = createTestClient()

        // Act
        // Assert response payload
        client.postVerification().apply {
            assertEquals(BadGateway, status)
            val body: ErrDTO = body()
            assertEquals(ErrType.BAD_GATEWAY.uri.toString(), body.type)
            assertEquals(ErrType.BAD_GATEWAY.title, body.title)
        }

        // Assert upstream requests
        assertUpstreamEndpoints(Endpoint.AOV_VERIFY)

        // TODO: assert logged
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("bodyAcceptingPaths")
    fun `malformed JSON body is rejected`(path: String) = testApplication {
        // Arrange
        setupApplication(upstreams())
        val client = createTestClient()

        // Act
        // Assert response payload
        client.postRaw(path, """{"exchangeID": """).assertIsError(UnprocessableEntity, ErrType.BAD_REQUEST)

        // Assert upstream requests
        assertUpstreamEndpoints()

        // Assert db logging
        assertNothingLogged()
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("bodyAcceptingPaths")
    fun `body missing required fields is rejected`(path: String) = testApplication {
        // Arrange
        setupApplication(upstreams())
        val client = createTestClient()

        // Act
        // Assert response payload
        client.postRaw(path, "{}").assertIsError(UnprocessableEntity, ErrType.BAD_REQUEST)

        // Assert upstream requests
        assertUpstreamEndpoints()

        // Assert db logging
        assertNothingLogged()
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("bodyAcceptingPaths")
    fun `body of an unsupported content type is rejected`(path: String) = testApplication {
        // Arrange
        setupApplication(upstreams())
        val client = createTestClient()

        // Act
        // Assert response payload
        client.postRaw(path, "not json at all", ContentType.Text.Plain)
            .assertIsError(UnsupportedMediaType, ErrType.UNSUPPORTED_MEDIA_TYPE)

        // Assert upstream requests
        assertUpstreamEndpoints()

        // Assert db logging
        assertNothingLogged()
    }

    // TODO: handle potential invalid results from VC manager
    // TODO: handle potential other errors from processing

    private suspend fun HttpResponse.assertIsError(expectedStatus: HttpStatusCode, expectedType: ErrType) {
        assertEquals(expectedStatus, status)
        val err: ErrDTO = body()
        assertEquals(expectedType.uri.toString(), err.type)
        assertEquals(expectedType.title, err.title)
        assertNotNull(err.detail, "error response should explain what was wrong with the request")
    }

    private fun assertNothingLogged() = coVerify(exactly = 0) { reqsRepo.add(any()) }

    private fun assertLogged(expected: RequestLog) {
        assertEquals(expected, capturedLog().copy(id = expected.id))
    }

    private fun assertErrorLogged() {
        assertNotNull(capturedLog().error)
    }

    private fun capturedLog(): RequestLog {
        val logged: CapturingSlot<RequestLog> = slot()
        coVerify(exactly = 1) { reqsRepo.add(capture(logged)) }
        confirmVerified(reqsRepo)
        return logged.captured
    }

    private fun assertUpstreamEndpoints(vararg expected: Endpoint) =
        assertEquals(expected.map { it.path }, sentRequests.map { it.endpointPath })

    private fun requestTo(endpoint: Endpoint): HttpRequestData =
        sentRequests.singleOrNull { it.endpointPath == endpoint.path }
            ?: fail("expected exactly one request to ${endpoint.path}, but sent ${sentRequests.map { it.endpointPath }}")

    private inline fun <reified T> sentBody(endpoint: Endpoint): T =
        Json.decodeFromString<T>((requestTo(endpoint).body as TextContent).text)

    private fun ApplicationTestBuilder.setupApplication(handle: suspend MockRequestHandleScope.(HttpRequestData) -> HttpResponseData) {
        setupTestApplication {
            val testModule = module {
                single<RequestLogRepo> { reqsRepo }
                single<Clock> { FixedClock }
                single<HttpClient> {
                    HttpClient(
                        MockEngine { req -> sentRequests += req; handle(req) }) { configureForUpstreams() }
                }
                single {
                    UpstreamClient(
                        http = get<HttpClient>(), Upstream.entries.associateWith { "http://${it.name.lowercase()}" })
                }
            }
            this.install(Koin) { modules(testModule) }

            aovRoutes()
        }
    }

    companion object {
        @JvmStatic
        fun bodyAcceptingPaths() = listOf("/attestation", "/attestation/verify")

        @JvmStatic
        fun attestationUpstreamTransportFailures() = listOf(
            Arguments.of("VLA manager unreachable", Endpoint.vla(vlaUUID), { ConnectException() }),
            Arguments.of("VLA manager unresolvable", Endpoint.vla(vlaUUID), { UnresolvedAddressException() }),
            Arguments.of("processing module unreachable", Endpoint.EVALUATE_BATCH, { ConnectException() }),
            Arguments.of("processing module unresolvable", Endpoint.EVALUATE_BATCH, { UnresolvedAddressException() }),
            Arguments.of("VC manager unreachable", Endpoint.AOV_ISSUE, { ConnectException() }),
            Arguments.of("VC manager unresolvable", Endpoint.AOV_ISSUE, { UnresolvedAddressException() }),
        )
    }
}