package hu.bme.mit.ftsrg.dva.api.testutil

import io.ktor.client.engine.mock.*
import io.ktor.client.request.*
import io.ktor.http.*
import kotlinx.serialization.json.Json

typealias MockResponder = suspend MockRequestHandleScope.(HttpRequestData) -> HttpResponseData

inline fun <reified T> MockRequestHandleScope.jsonResponse(body: T) =
    respond(
        content = Json.encodeToString(body),
        status = HttpStatusCode.OK,
        headersOf(HttpHeaders.ContentType, ContentType.Application.Json.toString())
    )