package hu.bme.mit.ftsrg.dva.api.err

import hu.bme.mit.ftsrg.dva.api.err.ErrType.NOT_FOUND
import hu.bme.mit.ftsrg.dva.dto.api.ErrDTO
import hu.bme.mit.ftsrg.dva.log.RequestLogError
import io.github.oshai.kotlinlogging.KotlinLogging
import io.ktor.http.HttpStatusCode.Companion.InternalServerError
import io.ktor.http.HttpStatusCode.Companion.NotFound
import io.ktor.server.application.*
import io.ktor.server.plugins.statuspages.*
import io.ktor.server.request.*
import io.ktor.server.response.*

private val logger = KotlinLogging.logger {}

fun StatusPagesConfig.addHandlers() {
    exception<Throwable>(::handleException)
    status(NotFound) { call, _ -> handleUnrouted(call) }
}

suspend fun handleException(call: ApplicationCall, cause: Throwable) {
    logger.atWarn {
        message = "Handling exception: $cause"
        this.cause = cause
        payload = mapOf("stacktrace" to cause.stackTraceToString())
    }

    val err = cause as? APIErr
    call.respond(
        status = err?.status ?: InternalServerError,
        message = call.toErrorDTO(err?.type ?: ErrType.UNKNOWN, err),
    )
}

/**
 * Handle a request to a path that is not routed in ktor.
 */
suspend fun handleUnrouted(call: ApplicationCall) {
    logger.atWarn {
        message = "Handling unrouted request error"
        payload = mapOf("path" to call.request.path())
    }
    call.respond(message = call.toErrorDTO(NOT_FOUND), status = NotFound)
}

private fun ApplicationCall.toErrorDTO(
    type: ErrType,
    cause: Throwable? = null,
): ErrDTO =
    errDTO(type) {
        instance = request.path()
    }.apply {
        if (cause != null) detail = cause.message
    }

fun Throwable.toRequestLogError(): RequestLogError {
    val err = this as? APIErr
    return RequestLogError(title = (err?.type ?: ErrType.UNKNOWN).title, detail = message)
}