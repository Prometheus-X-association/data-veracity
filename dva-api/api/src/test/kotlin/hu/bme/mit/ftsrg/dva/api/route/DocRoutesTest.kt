package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.testutil.setupTestApplication
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.server.testing.*
import org.junit.jupiter.api.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

private const val OPENAPI_PATH = "../../docs/spec/dva-api.yaml"

class DocRoutesTest {

    @Test
    fun `should return HTML page when root route is requested`() = testApplication {
        setupApplication()
        client.get("/").apply {
            assertEquals(HttpStatusCode.OK, status)
            assertTrue {
                headers["Content-Type"]?.contains(ContentType.Text.Html.toString()) ?: false
            }
        }
    }

    @Test
    fun `should return swagger documentation page when slash swagger is requested`() = testApplication {
        setupApplication()
        client.get("/swagger").apply {
            assertEquals(HttpStatusCode.OK, status)
            assertTrue {
                headers["Content-Type"]?.contains(ContentType.Text.Html.toString()) ?: false
            }
        }
    }

    @Test
    fun `should serve the openapi file itself`() = testApplication {
        setupApplication()
        client.get("/swagger/dva-api.yaml").apply {
            assertEquals(HttpStatusCode.OK, status)
            assertTrue(bodyAsText().contains("openapi: 3.1"))
        }
    }

    /** The spec `$ref`s `./components.yaml`, which Swagger UI fetches relative to the spec URL. */
    @Test
    fun `should serve documents the openapi file refers to`() = testApplication {
        setupApplication()
        client.get("/swagger/components.yaml").apply {
            assertEquals(HttpStatusCode.OK, status)
            assertTrue(bodyAsText().contains("EvaluationResult"))
        }
    }

    @Test
    fun `should not serve files outside the spec directory`() = testApplication {
        setupApplication()
        listOf("/swagger/..%2F..%2Fbuild.gradle.kts", "/swagger/nonexistent.yaml", "/swagger/.env").forEach {
            assertEquals(HttpStatusCode.NotFound, client.get(it).status, "should not have served $it")
        }
    }

    private fun ApplicationTestBuilder.setupApplication() =
        setupTestApplication { docRoutes(openapiPath = OPENAPI_PATH) }
}
