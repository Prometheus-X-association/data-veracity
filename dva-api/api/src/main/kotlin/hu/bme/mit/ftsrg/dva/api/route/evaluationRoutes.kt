package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.resource.Evaluation
import io.ktor.client.HttpClient
import io.ktor.client.request.*
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.server.application.Application
import io.ktor.server.request.receiveText
import io.ktor.server.resources.post
import io.ktor.server.response.respondText
import io.ktor.server.routing.routing
import org.koin.ktor.ext.inject

fun Application.evaluationRoutes() {
    val httpClient by inject<HttpClient>()

    val processingURL = environment.config.property("processing.url").getString()

    routing {
        post<Evaluation> {
            val response = httpClient.post("${processingURL}/evaluate") {
                setBody(call.receiveText())
                contentType(ContentType.Application.Json)
            }

            call.respondText(
                text = response.bodyAsText(),
                contentType = ContentType.Application.Json,
                status = response.status
            )
        }
    }
}
