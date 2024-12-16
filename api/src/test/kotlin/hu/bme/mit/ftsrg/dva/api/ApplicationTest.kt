package hu.bme.mit.ftsrg.dva.api

import hu.bme.mit.ftsrg.dva.api.error.ErrorType
import hu.bme.mit.ftsrg.dva.dto.generic.ErrorDTO
import io.ktor.client.call.*
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.testing.*
import org.junit.jupiter.api.Test
import kotlin.test.assertEquals
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation as ClientContentNegotiation

class ApplicationTest {

  @Test
  fun `should respond with not found error on nonexistent path requested`() = testApplication {
    application { module() }
    val client = createClient { install(ClientContentNegotiation) { json() } }
    client.get("/nonexistent").apply {
      assertEquals(HttpStatusCode.NotFound, status)
      assertEquals(ErrorType.NOT_FOUND.uri.path, body<ErrorDTO>().type)
    }
  }
}