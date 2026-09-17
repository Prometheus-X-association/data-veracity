package hu.bme.mit.ftsrg.dva.api.err

import io.ktor.http.*

class UnsupportedMediaTypeErr(cause: Throwable) : APIErr(
    ErrType.UNSUPPORTED_MEDIA_TYPE,
    HttpStatusCode.UnsupportedMediaType,
    cause.message ?: "Unsupported content type",
    cause,
)