package hu.bme.mit.ftsrg.dva.api.upstream

import hu.bme.mit.ftsrg.dva.api.upstream.Upstream.*
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.plugins.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.serialization.*
import io.ktor.serialization.kotlinx.json.*
import io.ktor.util.network.*
import kotlinx.io.IOException
import kotlinx.serialization.json.Json
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

enum class Upstream(val configKey: String) {
    VLA_MANAGER("vlaManager.url"),
    PROCESSING("processing.url"),
    VC_MANAGER("vcManager.url"),
}

data class Endpoint(val service: Upstream, val path: String) {
    companion object {
        @OptIn(ExperimentalUuidApi::class)
        fun vla(id: Uuid) = Endpoint(VLA_MANAGER, "vla/$id")
        val EVALUATE_BATCH = Endpoint(PROCESSING, "evaluate-batch")
        val AOV_ISSUE = Endpoint(VC_MANAGER, "aov/issue")
        val AOV_VERIFY = Endpoint(VC_MANAGER, "aov/verify")
    }
}

class UpstreamClient(
    @PublishedApi internal val http: HttpClient,
    @PublishedApi internal val baseURLs: Map<Upstream, String>,
) {
    suspend inline fun <reified T> call(
        endpoint: Endpoint,
        method: HttpMethod = HttpMethod.Get,
        noinline mapStatus: (HttpStatusCode) -> Throwable? = { null },
        noinline configure: HttpRequestBuilder.() -> Unit = {},
    ): T = try {
        http.request("${baseURLs.getValue(endpoint.service)}/${endpoint.path}") {
            this.method = method
            contentType(ContentType.Application.Json)
            accept(ContentType.Application.Json)
            configure()
        }.body<T>()
    } catch (e: ResponseException) {
        throw mapStatus(e.response.status) ?: UpstreamErr.BadStatus(
            endpoint.service,
            e.response.status,
            e.response.bodyAsText(),
            e
        )
    } catch (e: UnresolvedAddressException) {
        throw UpstreamErr.Unreachable(endpoint.service, e)
    } catch (e: IOException) {
        throw UpstreamErr.Unreachable(endpoint.service, e)
    } catch (e: JsonConvertException) {
        throw UpstreamErr.BadBody(endpoint.service, e)
    }
}

fun HttpClientConfig<*>.configureForUpstreams() {
    expectSuccess = true
    install(ContentNegotiation) {
        json(Json {
            explicitNulls = true
            ignoreUnknownKeys = true
        })
    }
}