package hu.bme.mit.ftsrg.dva.api.error

import hu.bme.mit.ftsrg.dva.api.error.ErrorType.NOT_FOUND
import hu.bme.mit.ftsrg.dva.api.error.ErrorType.UNKNOWN
import hu.bme.mit.ftsrg.dva.dto.generic.ErrorDTO
import io.ktor.http.HttpStatusCode.Companion.InternalServerError
import io.ktor.http.HttpStatusCode.Companion.NotFound
import io.ktor.server.application.*
import io.ktor.server.plugins.statuspages.*
import io.ktor.server.request.*
import io.ktor.server.response.*

fun StatusPagesConfig.addHandlers() {
  exception<Throwable>(::handleException)
  status(NotFound) { call, _ -> handleNotFound(call) }
}

suspend fun handleException(call: ApplicationCall, cause: Throwable) {
  when (cause) {
    else -> {
      call.respond(message = call.toErrorDTO(UNKNOWN), status = InternalServerError)
    }
  }
}

suspend fun handleNotFound(call: ApplicationCall) {
  call.respond(message = call.toErrorDTO(NOT_FOUND), status = NotFound)
}

private fun ApplicationCall.toErrorDTO(type: ErrorType, init: ErrorDTO.() -> Unit = {}): ErrorDTO =
  errorDTO(type) { instance = request.path() }.apply(init)