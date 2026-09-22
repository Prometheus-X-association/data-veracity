package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.health.Dependency
import hu.bme.mit.ftsrg.dva.api.health.HealthJSON
import hu.bme.mit.ftsrg.dva.api.health.Readiness
import hu.bme.mit.ftsrg.dva.api.health.ServiceHealth
import hu.bme.mit.ftsrg.dva.api.health.gatewayDependencies
import hu.bme.mit.ftsrg.dva.api.testutil.setupTestApplication
import hu.bme.mit.ftsrg.dva.api.upstream.Upstream
import hu.bme.mit.ftsrg.dva.api.upstream.UpstreamClient
import hu.bme.mit.ftsrg.dva.api.upstream.configureForUpstreams
import hu.bme.mit.ftsrg.dva.dto.common.Health
import hu.bme.mit.ftsrg.dva.dto.common.HealthStatus
import io.ktor.client.*
import io.ktor.client.engine.mock.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.testing.*
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test
import org.koin.dsl.module
import org.koin.ktor.plugin.Koin
import java.net.ConnectException
import kotlin.time.Duration.Companion.milliseconds

private val ok = Dependency("ok") {}

class HealthRoutesTest {

    @Test
    fun `livez passes without checking anything`() = testApplication {
        setupApplication(Dependency("postgres") { error("down") })

        client.get("/livez").apply {
            assertEquals(HttpStatusCode.OK, status)
            assertEquals(HealthJSON, contentType()?.withoutParameters())
            assertEquals("""{"status":"pass"}""", bodyAsText())
        }
    }

    @Test
    fun `readyz passes when every dependency answers`() = testApplication {
        setupApplication(ok, ok)

        client.get("/readyz").apply {
            assertEquals(HttpStatusCode.OK, status)
            assertEquals("""{"status":"pass"}""", bodyAsText())
        }
    }

    @Test
    fun `readyz fails with 503 and says why`() = testApplication {
        setupApplication(ok, Dependency("postgres") { error("connection refused") }, Dependency("processing") {
            delay(10_000)
        })

        client.get("/readyz").apply {
            assertEquals(HttpStatusCode.ServiceUnavailable, status)
            assertEquals(
                """{"status":"fail","output":"postgres: connection refused; processing: timed out"}""",
                bodyAsText()
            )
        }
    }

    @Test
    fun `upstreams are checked through their livez`() {
        val asked = mutableListOf<String>()
        val upstreams = UpstreamClient(
            http = HttpClient(MockEngine { req ->
                asked += req.url.toString()
                when (req.url.host) {
                    "processing" -> respondError(HttpStatusCode.ServiceUnavailable)
                    "vc_manager" -> throw ConnectException("Connection refused")
                    else -> respond("""{"status":"pass"}""")
                }
            }) { configureForUpstreams() },
            baseURLs = Upstream.entries.associateWith { "http://${it.name.lowercase()}" },
        )
        // Postgres is left out: no test connects a database.
        val health = runBlocking {
            Readiness(gatewayDependencies(upstreams).filter { it.name != "postgres" }).check()
        }

        assertEquals(
            setOf("http://vla_manager/livez", "http://processing/livez", "http://vc_manager/livez"),
            asked.toSet()
        )
        assertEquals(HealthStatus.FAIL, health.status)
        assertEquals("processing: answered 503 Service Unavailable; vc-manager: Connection refused", health.output)
    }

    @Test
    fun `service health collects every service's readyz`() {
        val upstreams = UpstreamClient(
            http = HttpClient(MockEngine { req ->
                assertEquals("/readyz", req.url.encodedPath)
                when (req.url.host) {
                    "processing" -> respond(
                        """{"status":"fail","output":"postgres: down"}""", HttpStatusCode.ServiceUnavailable
                    )
                    "vc_manager" -> throw ConnectException("Connection refused")
                    else -> respond("""{"status":"warn","output":"in memory"}""")
                }
            }) { configureForUpstreams() },
            baseURLs = Upstream.entries.associateWith { "http://${it.name.lowercase()}" },
        )

        val health = runBlocking { ServiceHealth(Readiness(listOf(ok)), upstreams).check() }

        assertEquals(
            mapOf(
                "gateway" to Health(HealthStatus.PASS),
                "vla-manager" to Health(HealthStatus.WARN, "in memory"),
                "processing" to Health(HealthStatus.FAIL, "postgres: down"),
                "vc-manager" to Health(HealthStatus.FAIL, "Connection refused"),
            ),
            health
        )
    }

    private fun ApplicationTestBuilder.setupApplication(vararg dependencies: Dependency) = setupTestApplication {
        this.install(Koin) {
            modules(module { single { Readiness(dependencies.toList(), timeout = 50.milliseconds) } })
        }
        healthRoutes()
    }
}
