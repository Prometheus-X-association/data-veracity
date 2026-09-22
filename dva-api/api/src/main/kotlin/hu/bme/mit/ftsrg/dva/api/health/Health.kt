package hu.bme.mit.ftsrg.dva.api.health

import hu.bme.mit.ftsrg.dva.api.upstream.Upstream
import hu.bme.mit.ftsrg.dva.api.upstream.UpstreamClient
import hu.bme.mit.ftsrg.dva.dto.common.Health
import hu.bme.mit.ftsrg.dva.dto.common.HealthStatus
import io.ktor.client.plugins.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.response.*
import kotlinx.coroutines.*
import kotlinx.serialization.json.Json
import org.jetbrains.exposed.v1.jdbc.transactions.experimental.newSuspendedTransaction
import kotlin.coroutines.cancellation.CancellationException
import kotlin.time.Duration
import kotlin.time.Duration.Companion.seconds

val HealthJSON: ContentType = ContentType("application", "health+json")

/** Something `/readyz` depends on; [ping] throws when it is not healthy. */
class Dependency(val name: String, val ping: suspend () -> Unit)

/** Pings every dependency concurrently; any that errs or does not answer in time fails readiness. */
class Readiness(private val dependencies: List<Dependency>, private val timeout: Duration = 2.seconds) {
    suspend fun check(): Health {
        val problems: List<String> =
            coroutineScope { dependencies.map { async { problem(it) } }.awaitAll() }.filterNotNull()
        return if (problems.isEmpty()) Health(HealthStatus.PASS)
        else Health(HealthStatus.FAIL, problems.joinToString("; "))
    }

    private suspend fun problem(dependency: Dependency): String? = try {
        withTimeout(timeout) { dependency.ping() }
        null
    } catch (_: TimeoutCancellationException) {
        "${dependency.name}: timed out"
    } catch (e: CancellationException) {
        throw e
    } catch (e: Exception) {
        "${dependency.name}: ${e.message ?: e::class.simpleName}"
    }
}

fun gatewayDependencies(upstreams: UpstreamClient): List<Dependency> =
    listOf(Dependency("postgres") {
        newSuspendedTransaction(Dispatchers.IO) {
            // JDBC ignores coroutine cancellation, so the query has to time out on its own.
            queryTimeout = 2
            exec("SELECT 1")
        }
    }) + Upstream.entries.map { svc ->
        Dependency(svc.label) {
            val status: HttpStatusCode =
                upstreams.http.get("${upstreams.baseURLs.getValue(svc)}/livez") { expectSuccess = false }.status
            check(status.isSuccess()) { "answered $status" }
        }
    }

/** eg `vla-manager` for [Upstream.VLA_MANAGER] */
val Upstream.label: String get() = name.lowercase().replace('_', '-')

/**
 * The `/readyz` of the gateway and of every upstream, keyed `gateway` and [Upstream.label], for
 * the dashboard, which can only reach the gateway.  An upstream that does not answer with a
 * health report in time counts as `fail`.
 */
class ServiceHealth(
    private val readiness: Readiness,
    private val upstreams: UpstreamClient,
    private val timeout: Duration = 2.seconds,
) {
    suspend fun check(): Map<String, Health> = coroutineScope {
        val gateway = async { "gateway" to readiness.check() }
        val others = Upstream.entries.map { svc -> async { svc.label to readyz(svc) } }
        (listOf(gateway) + others).awaitAll().toMap()
    }

    private suspend fun readyz(svc: Upstream): Health = try {
        withTimeout(timeout) {
            val response = upstreams.http.get("${upstreams.baseURLs.getValue(svc)}/readyz") { expectSuccess = false }
            // A `fail` comes as a 503 that still carries the report.
            if (response.status != HttpStatusCode.OK && response.status != HttpStatusCode.ServiceUnavailable) {
                Health(HealthStatus.FAIL, "answered ${response.status}")
            } else {
                lenient.decodeFromString<Health>(response.bodyAsText())
            }
        }
    } catch (_: TimeoutCancellationException) {
        Health(HealthStatus.FAIL, "timed out")
    } catch (e: CancellationException) {
        throw e
    } catch (e: Exception) {
        Health(HealthStatus.FAIL, e.message ?: e::class.simpleName)
    }

    private companion object {
        val lenient = Json { ignoreUnknownKeys = true }
    }
}

private val json = Json { explicitNulls = false }

/** Serve [health], answering 503 exactly when it is `fail`. */
suspend fun ApplicationCall.respondHealth(health: Health) = respondText(
    text = json.encodeToString(health),
    contentType = HealthJSON,
    status = if (health.status == HealthStatus.FAIL) HttpStatusCode.ServiceUnavailable else HttpStatusCode.OK,
)
