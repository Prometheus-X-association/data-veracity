package hu.bme.mit.ftsrg.dva.api

import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.server.testing.*
import org.junit.jupiter.api.Test
import kotlin.test.*

class ApplicationTest {
  @Test
  fun testRoot() = testApplication {
    application {
      module()
    }
    val resp: HttpResponse = client.get("/")
    assertEquals(HttpStatusCode.OK, resp.status)
    assertEquals("Hello World!", resp.bodyAsText())
  }
}