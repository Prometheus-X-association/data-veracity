package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.resource.Info
import hu.bme.mit.ftsrg.dva.log.ReqestLogRepo
import io.ktor.server.application.*
import io.ktor.server.resources.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import org.koin.ktor.ext.inject

fun Application.infoRoutes() {
    val reqsRepo by inject<ReqestLogRepo>()

    routing {
        get<Info.Requests> { call.respond(reqsRepo.all()) }
    }
}