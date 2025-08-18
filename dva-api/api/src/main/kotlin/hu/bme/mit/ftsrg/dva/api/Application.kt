package hu.bme.mit.ftsrg.dva.api

import com.rabbitmq.client.Connection
import com.rabbitmq.client.ConnectionFactory
import hu.bme.mit.ftsrg.dva.api.error.addHandlers
import hu.bme.mit.ftsrg.dva.api.rabbit.connectWithRetry
import hu.bme.mit.ftsrg.dva.api.route.aovRoutes
import hu.bme.mit.ftsrg.dva.api.route.docRoutes
import hu.bme.mit.ftsrg.dva.api.route.templateRoutes
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
import org.litote.kmongo.coroutine.CoroutineDatabase
import org.litote.kmongo.coroutine.coroutine
import org.litote.kmongo.reactivestreams.KMongo
import org.slf4j.event.Level
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation as ClientContentNegotiation
import io.ktor.server.application.install as serverInstall
import io.ktor.server.plugins.contentnegotiation.ContentNegotiation as ServerContentNegotiation

fun main(args: Array<String>): Unit = EngineMain.main(args)

fun Application.module() {
    installPlugins()
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

    serverInstall(Koin)
}

fun Application.configureKoin() {
    val rabbitHost = environment.config.property("rabbitmq.host").getString()
    val mongoHost = environment.config.property("mongodb.host").getString()
    val mongoDB = environment.config.property("mongodb.database").getString()

    val appModule = module {
        single<Connection> {
            ConnectionFactory().run {
                host = rabbitHost
                connectWithRetry(logger = log)
            }
        }
        single<CoroutineDatabase> {
            KMongo.createClient("mongodb://$mongoHost:27017").coroutine.run {
                getDatabase(mongoDB)
            }
        }
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
    }

    serverInstall(Koin) { modules(appModule) }
}

fun Application.addRoutes() {
    docRoutes(openapiPath = environment.config.property("swagger.openapiFile").getString())
    templateRoutes()
    aovRoutes()
}