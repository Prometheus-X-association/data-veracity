package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.error.ErrorType
import hu.bme.mit.ftsrg.dva.api.testutil.testModule
import hu.bme.mit.ftsrg.dva.dto.ErrorDTO
import hu.bme.mit.ftsrg.dva.dto.IDDTO
import hu.bme.mit.ftsrg.dva.model.vla.*
import hu.bme.mit.ftsrg.dva.persistence.repository.fake.FakeVLATemplateRepository
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.testing.*
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation as ClientContentNegotiation

/* TODO: These tests should not be coupled with FakeVLATemplateRepository */
class TemplateRoutesTest {

  @Test
  fun `should respond with list of templates`() = testApplication {
    setupApplication()
    val client = setupClient()

    client.get("/template").apply {
      val templates: List<VLATemplate> = body()
      assertEquals(HttpStatusCode.OK, status)
      assertTrue { templates.isNotEmpty() }
    }
  }

  @Test
  fun `should create new template`() = testApplication {
    setupApplication()
    val client = setupClient()

    val template = VLATemplate(
      id = "template-test-0",
      objective = VeracityObjective(
        evaluationScheme = EvaluationScheme(
          evaluationMethod = "syntax_check",
          criterionType = CriterionType.VALID_INVALID
        ),
        targetAspect = QualityAspect.SYNTAX,
      ),
    )

    client.post("/template") {
      contentType(ContentType.Application.Json)
      setBody(template)
    }.apply {
      val idDTO: IDDTO = body()
      assertEquals(HttpStatusCode.Created, status)
      assertEquals(template.id, idDTO.id)
    }
  }

  @Test
  fun `should not allow creation of template with existing ID`() = testApplication {
    setupApplication()
    val client = setupClient()

    val template = VLATemplate(
      id = "template-0001",
      objective = VeracityObjective(
        evaluationScheme = EvaluationScheme(
          evaluationMethod = "syntax_check",
          criterionType = CriterionType.VALID_INVALID
        ),
        targetAspect = QualityAspect.SYNTAX,
      ),
    )

    client.post("/template") {
      contentType(ContentType.Application.Json)
      setBody(template)
    }.apply {
      val err: ErrorDTO = body()
      assertEquals(HttpStatusCode.BadRequest, status)
      assertEquals(err.type, ErrorType.ALREADY_EXISTS.uri.path)
    }
  }

  @Test
  fun `should respond with existing template if exists`() = testApplication {
    setupApplication()
    val client = setupClient()

    val id = "template-0001"
    client.get("/template/$id").apply {
      val template: VLATemplate = body()
      assertEquals(HttpStatusCode.OK, status)
      assertEquals(id, template.id)
    }
  }

  @Test
  fun `should respond with not found error when attempting to read nonexistent template`() = testApplication {
    setupApplication()
    val client = setupClient()

    val id = "non-existent"
    client.get("/template/$id").apply {
      val err: ErrorDTO = body()
      assertEquals(HttpStatusCode.NotFound, status)
      assertEquals(err.type, ErrorType.NOT_FOUND.uri.path)
    }
  }

  @Test
  fun `should delete existing template`() = testApplication {
    setupApplication()
    val client = setupClient()

    val id = "template-0001"
    client.delete("/template/$id").apply {
      assertEquals(HttpStatusCode.OK, status)
    }
    client.get("/template/$id").apply {
      assertEquals(HttpStatusCode.NotFound, status)
    }
  }

  @Test
  fun `should respond with not found error when attempting to delete nonexistent `() = testApplication {
    setupApplication()
    val client = setupClient()

    val id = "non-existent"
    client.delete("/template/$id").apply {
      assertEquals(HttpStatusCode.NotFound, status)
    }
  }
}

private fun ApplicationTestBuilder.setupApplication() = application {
  testModule()
  templateRoutes(FakeVLATemplateRepository())
}

private fun ApplicationTestBuilder.setupClient(): HttpClient = createClient {
  install(ClientContentNegotiation) { json() }
}