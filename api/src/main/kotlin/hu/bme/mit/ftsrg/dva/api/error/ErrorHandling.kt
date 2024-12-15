package hu.bme.mit.ftsrg.dva.api.error

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.plugins.statuspages.*
import io.ktor.server.response.*

fun StatusPagesConfig.addHandlers() {
  exception<Throwable>(::handleException)
  status(HttpStatusCode.NotFound) { call, _ -> handleNotFound(call) }
}

suspend fun handleException(call: ApplicationCall, cause: Throwable) {
  when (cause) {
    else -> call.respondText("Unknown error", status = HttpStatusCode.InternalServerError)
  }
}

suspend fun handleNotFound(call: ApplicationCall) {
  call.respondText("The requested resource was not found", status = HttpStatusCode.NotFound)
}