package hu.bme.mit.ftsrg.dva.api.error

import hu.bme.mit.ftsrg.dva.api.error.ErrorType.*
import hu.bme.mit.ftsrg.dva.dto.ErrorDTO
import io.github.oshai.kotlinlogging.KotlinLogging
import io.ktor.http.HttpStatusCode.Companion.InternalServerError
import io.ktor.http.HttpStatusCode.Companion.NotFound
import io.ktor.http.HttpStatusCode.Companion.NotImplemented
import io.ktor.server.application.*
import io.ktor.server.plugins.statuspages.*
import io.ktor.server.request.*
import io.ktor.server.response.*

private val logger = KotlinLogging.logger {}

fun StatusPagesConfig.addHandlers() {
    exception<Throwable>(::handleException)
    status(NotFound) { call, _ -> handleNotFound(call) }
}

suspend fun handleException(call: ApplicationCall, cause: Throwable) {
    logger.atWarn {
        message = "Handling exception: $cause"
        this.cause = cause
        payload = mapOf("stacktrace" to cause.stackTraceToString())
    }

    when (cause) {
        is UnimplementedError -> {
            call.respond(message = call.toErrorDTO(UNIMPLEMENTED, cause), status = NotImplemented)
        }

        else -> {
            call.respond(message = call.toErrorDTO(UNKNOWN, cause), status = InternalServerError)
        }
    }
}

suspend fun handleNotFound(call: ApplicationCall) {
    logger.atWarn {
        message = "Handling not found error"
        payload = mapOf("path" to call.request.path())
    }
    call.respond(message = call.toErrorDTO(NOT_FOUND), status = NotFound)
}

private fun ApplicationCall.toErrorDTO(
    type: ErrorType,
    cause: Throwable? = null,
    init: ErrorDTO.() -> Unit = {}
): ErrorDTO =
    errorDTO(type) {
        instance = request.path()
    }.apply {
        if (cause != null) detail = "${cause.message}\n\nStack Trace:\n${cause.stackTraceToString()}"
    }.apply(init)