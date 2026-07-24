package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.resource.Attestations
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.resources.post
import io.ktor.server.routing.*
import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi

@OptIn(ExperimentalTime::class, ExperimentalUuidApi::class)
fun Application.aovRoutes() {
    // val reqsRepo by inject<ReqestLogRepo>()

    routing {
        post<Attestations> {
            // TODO: Needs reimplementation since removal of RMQ
            call.response.status(HttpStatusCode.NotImplemented)
        }

        post<Attestations.Verify> {
            // TODO: Needs reimplementation since removal of ACA-Py
            call.response.status(HttpStatusCode.NotImplemented)
        }
    }
}