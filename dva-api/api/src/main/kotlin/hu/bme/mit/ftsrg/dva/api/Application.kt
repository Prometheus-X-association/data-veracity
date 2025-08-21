package hu.bme.mit.ftsrg.dva.api

import hu.bme.mit.ftsrg.dva.api.db.PgRequestLogRepo
import hu.bme.mit.ftsrg.dva.api.db.PgTemplateRepo
import hu.bme.mit.ftsrg.dva.api.db.PgVerifRequestLogRepo
import hu.bme.mit.ftsrg.dva.api.db.configureDatabases
import hu.bme.mit.ftsrg.dva.api.err.addHandlers
import hu.bme.mit.ftsrg.dva.api.route.aovRoutes
import hu.bme.mit.ftsrg.dva.api.route.docRoutes
import hu.bme.mit.ftsrg.dva.api.route.infoRoutes
import hu.bme.mit.ftsrg.dva.api.route.templateRoutes
import hu.bme.mit.ftsrg.dva.log.ReqestLogRepo
import hu.bme.mit.ftsrg.dva.log.VerifRequestLogRepo
import hu.bme.mit.ftsrg.dva.vla.TemplateRepo
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
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation as ClientContentNegotiation
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

fun Application.configureKoin() {
    val rabbitHost = environment.config.property("rabbitmq.host").getString()

    val appModule = module {
        //single<Connection> {
        //    ConnectionFactory().run {
        //        host = rabbitHost
        //        connectWithRetry(logger = log)
        //    }
        //}
        single<HttpClient> {
            HttpClient(CIO) {
                install(ClientContentNegotiation) {
                    json(Json {
                        explicitNulls = true
                        ignoreUnknownKeys = true
                    })
                }
            }
        }
        single<TemplateRepo> { PgTemplateRepo() }
        single<ReqestLogRepo> { PgRequestLogRepo() }
        single<VerifRequestLogRepo> { PgVerifRequestLogRepo() }
    }

    serverInstall(Koin) { modules(appModule) }
}

fun Application.addRoutes() {
    docRoutes(openapiPath = environment.config.property("swagger.openapiFile").getString())
    templateRoutes()
    aovRoutes()
    infoRoutes()
}