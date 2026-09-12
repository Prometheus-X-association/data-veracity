package hu.bme.mit.ftsrg.dva.api.testutil

import hu.bme.mit.ftsrg.dva.api.installPlugins
import io.ktor.client.*
import io.ktor.client.plugins.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.application.*
import io.ktor.server.testing.*
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation as ClientContentNegotiation

fun ApplicationTestBuilder.setupTestApplication(block: Application.() -> Unit = {}) = application {
    setupApplicationBase()
    block()
}

fun ApplicationTestBuilder.createTestClient(block: HttpClientConfig<*>.() -> Unit = {}): HttpClient = createClient {
    defaultRequest { contentType(ContentType.Application.Json) }
    install(ClientContentNegotiation) { json() }
    block()
}

private fun Application.setupApplicationBase() = installPlugins()
