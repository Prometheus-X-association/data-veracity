package hu.bme.mit.ftsrg.dva.api.err

import io.ktor.http.*

class MalformedRequestErr(cause: Throwable) : APIErr(
    ErrType.BAD_REQUEST,
    HttpStatusCode.UnprocessableEntity,
    "Malformed request body: ${cause.rootCause().message}",
    cause,
)

private fun Throwable.rootCause(): Throwable = generateSequence(this) { it.cause }.last()