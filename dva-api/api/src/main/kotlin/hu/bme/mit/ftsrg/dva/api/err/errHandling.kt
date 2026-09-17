package hu.bme.mit.ftsrg.dva.api.err

import hu.bme.mit.ftsrg.dva.api.err.ErrType.NOT_FOUND
import hu.bme.mit.ftsrg.dva.api.err.ErrType.UNSUPPORTED_MEDIA_TYPE
import hu.bme.mit.ftsrg.dva.dto.api.ErrDTO
import hu.bme.mit.ftsrg.dva.log.RequestLogError
import io.github.oshai.kotlinlogging.KotlinLogging
import io.ktor.http.*
import io.ktor.http.HttpStatusCode.Companion.InternalServerError
import io.ktor.http.HttpStatusCode.Companion.NotFound
import io.ktor.http.HttpStatusCode.Companion.UnsupportedMediaType
import io.ktor.server.application.*
import io.ktor.server.plugins.*
import io.ktor.server.plugins.ContentTransformationException
import io.ktor.server.plugins.statuspages.*
import io.ktor.server.request.*
import io.ktor.server.response.*

private val logger = KotlinLogging.logger {}

fun StatusPagesConfig.addHandlers() {
    exception<Throwable>(::handleException)
    status(NotFound) { call, _ -> handleUnrouted(call) }
    status(UnsupportedMediaType) { call, _ -> handleUnsupportedMediaType(call) }
}

suspend fun handleException(call: ApplicationCall, cause: Throwable) {
    logger.atWarn {
        message = "Handling exception: $cause"
        this.cause = cause
        payload = mapOf("stacktrace" to cause.stackTraceToString())
    }

    val err: APIErr? = cause.asAPIErr()
    call.respond(
        status = err?.status ?: InternalServerError,
        message = call.toErrorDTO(err?.type ?: ErrType.UNKNOWN, err?.message),
    )
}

/**
 * The [APIErr] this throwable represents, or `null` if it is not something the API knows how to
 * report (i.e. it is a bug, and the client gets a 500).
 *
 * Ktor signals a client-side problem with its own exception types rather than with an [APIErr];
 * without translating them here, [StatusPagesConfig.exception] would catch them as generic
 * throwables and report a malformed request body as an internal server error.
 */
private fun Throwable.asAPIErr(): APIErr? = when (this) {
    is APIErr -> this
    is UnsupportedMediaTypeException -> UnsupportedMediaTypeErr(this)
    is BadRequestException, is ContentTransformationException -> MalformedRequestErr(this)
    else -> null
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

/**
 * Handle a request whose body content type no converter is registered for.
 *
 * Content negotiation answers these itself - with a bare 415 and no body - instead of throwing, so
 * [handleException] never sees them; we replace that empty response with an [ErrDTO] here.
 */
suspend fun handleUnsupportedMediaType(call: ApplicationCall) {
    val contentType: ContentType = call.request.contentType()
    logger.atWarn {
        message = "Handling unsupported media type error"
        payload = mapOf("path" to call.request.path(), "contentType" to contentType.toString())
    }
    call.respond(
        status = UnsupportedMediaType,
        message = call.toErrorDTO(
            UNSUPPORTED_MEDIA_TYPE,
            "Cannot read a request body of type $contentType; use ${ContentType.Application.Json}",
        ),
    )
}

private fun ApplicationCall.toErrorDTO(
    type: ErrType,
    detail: String? = null,
): ErrDTO =
    errDTO(type) { instance = request.path() }.apply { this.detail = detail }

fun Throwable.toRequestLogError(): RequestLogError {
    val err: APIErr? = asAPIErr()
    return RequestLogError(title = (err?.type ?: ErrType.UNKNOWN).title, detail = (err ?: this).message)
}