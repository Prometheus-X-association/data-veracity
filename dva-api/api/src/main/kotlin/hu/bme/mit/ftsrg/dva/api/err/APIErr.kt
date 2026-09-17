package hu.bme.mit.ftsrg.dva.api.err

import io.ktor.http.*

abstract class APIErr(val type: ErrType, val status: HttpStatusCode, message: String, cause: Throwable? = null) :
    RuntimeException(message, cause)