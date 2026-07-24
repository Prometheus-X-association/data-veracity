package hu.bme.mit.ftsrg.dva.api

import hu.bme.mit.ftsrg.dva.api.db.PgRequestLogRepo
import hu.bme.mit.ftsrg.dva.api.db.configureDatabases
import hu.bme.mit.ftsrg.dva.api.err.addHandlers
import hu.bme.mit.ftsrg.dva.api.route.aovRoutes
import hu.bme.mit.ftsrg.dva.api.route.docRoutes
import hu.bme.mit.ftsrg.dva.api.route.infoRoutes
import hu.bme.mit.ftsrg.dva.api.upstream.Upstream
import hu.bme.mit.ftsrg.dva.api.upstream.UpstreamClient
import hu.bme.mit.ftsrg.dva.api.upstream.configureForUpstreams
import hu.bme.mit.ftsrg.dva.log.RequestLogRepo
import io.ktor.client.*
import io.ktor.client.engine.cio.CIO
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.application.*
import io.ktor.server.cio.*
import io.ktor.server.plugins.calllogging.*
import io.ktor.server.plugins.statuspages.*
import io.ktor.server.request.*
import io.ktor.server.resources.*
import kotlinx.serialization.json.Json
import org.koin.dsl.module
import org.koin.ktor.plugin.Koin
import org.slf4j.event.Level
import kotlin.time.Clock
import kotlin.time.ExperimentalTime
import io.ktor.server.application.install as serverInstall
import io.ktor.server.plugins.contentnegotiation.ContentNegotiation as ServerContentNegotiation

fun main(args: Array<String>): Unit = EngineMain.main(args)

fun Application.module() {
    installPlugins()
    configureDatabases()
    configureKoin()
    addRoutes()
}

fun Application.installPlugins() {
    serverInstall(CallLogging) {
        level = Level.DEBUG
        format { call ->
            val status: HttpStatusCode? = call.response.status()
            val method = call.request.httpMethod.value
            val path: String = call.request.path()
            val time: Long = call.processingTimeMillis()
            val size: String? = call.response.headers["Content-Length"]

            val sizeStr = size?.let { " with body of $it bytes" } ?: ""

            "$method $path -> $status in $time ms$sizeStr"
        }
    }

    serverInstall(StatusPages) { addHandlers() }

    serverInstall(ServerContentNegotiation) { json(Json { explicitNulls = true }) }

    serverInstall(Resources)
}

@OptIn(ExperimentalTime::class)
fun Application.configureKoin() {
    val upstreamURLs: Map<Upstream, String> =
        Upstream.entries.associateWith { environment.config.property(it.configKey).getString() }
    val appModule = module {
        single<HttpClient> { HttpClient(CIO) { configureForUpstreams() } }
        single<RequestLogRepo> { PgRequestLogRepo() }
        single<Clock> { Clock.System }
        single { UpstreamClient(http = get<HttpClient>(), baseURLs = upstreamURLs) }
    }

    serverInstall(Koin) { modules(appModule) }
}

fun Application.addRoutes() {
    docRoutes(openapiPath = environment.config.property("swagger.openapiFile").getString())
    aovRoutes()
    infoRoutes()
}
