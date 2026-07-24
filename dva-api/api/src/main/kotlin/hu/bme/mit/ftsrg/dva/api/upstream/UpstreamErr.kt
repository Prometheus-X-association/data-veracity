package hu.bme.mit.ftsrg.dva.api.upstream

import hu.bme.mit.ftsrg.dva.api.err.APIErr
import hu.bme.mit.ftsrg.dva.api.err.ErrType
import io.ktor.http.*

sealed class UpstreamErr(val service: Upstream, message: String, cause: Throwable? = null) :
    APIErr(ErrType.BAD_GATEWAY, HttpStatusCode.BadGateway, message, cause) {

    class Unreachable(service: Upstream, cause: Throwable) :
        UpstreamErr(service, "$service unreachable: ${cause.message}", cause)

    class BadStatus(service: Upstream, val upstreamStatus: HttpStatusCode, val body: String, cause: Throwable) :
        UpstreamErr(service, "$service returned $upstreamStatus", cause)

    class BadBody(service: Upstream, cause: Throwable) :
        UpstreamErr(service, "$service returned an unreadable body: ${cause.message}", cause)

    class UnexpectedBody(service: Upstream, reason: String) :
        UpstreamErr(service, "$service returned an unexpected body: $reason")
}
