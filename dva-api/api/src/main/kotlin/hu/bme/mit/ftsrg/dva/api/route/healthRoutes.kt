package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.health.Readiness
import hu.bme.mit.ftsrg.dva.api.health.ServiceHealth
import hu.bme.mit.ftsrg.dva.api.health.respondHealth
import hu.bme.mit.ftsrg.dva.dto.common.Health
import hu.bme.mit.ftsrg.dva.dto.common.HealthStatus
import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import org.koin.ktor.ext.inject

fun Application.healthRoutes() {
    val readiness by inject<Readiness>()
    val serviceHealth by inject<ServiceHealth>()

    routing {
        get("/livez") { call.respondHealth(Health(HealthStatus.PASS)) }
        get("/readyz") { call.respondHealth(readiness.check()) }
        get("/info/health") { call.respond(serviceHealth.check()) }
    }
}
