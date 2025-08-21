package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.resource.Info
import hu.bme.mit.ftsrg.dva.log.DVARequestLogRepository
import hu.bme.mit.ftsrg.dva.log.DVAVerificationRequestLogRepository
import io.ktor.client.*
import io.ktor.client.request.*
import io.ktor.server.application.*
import io.ktor.server.resources.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import org.koin.ktor.ext.inject

fun Application.infoRoutes() {
    val reqsRepo by inject<DVARequestLogRepository>()
    val verifsRepo by inject<DVAVerificationRequestLogRepository>()
    val httpClient by inject<HttpClient>()

    val acaPyAgentURL = environment.config.property("acaPy.agent.url").getString()

    routing {
        get<Info.Requests> { call.respond(reqsRepo.allRequests()) }
        get<Info.Presentations> { call.respond(verifsRepo.allRequests()) }
        get<Info.Credentials> { call.respond(httpClient.get("$acaPyAgentURL/credentials")) }
    }
}
