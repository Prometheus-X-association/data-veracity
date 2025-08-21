package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.testutil.testModule
import hu.bme.mit.ftsrg.dva.dto.IDDTO
import hu.bme.mit.ftsrg.dva.vla.*
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.http.ContentType.*
import io.ktor.http.HttpStatusCode.Companion.Created
import io.ktor.http.HttpStatusCode.Companion.NoContent
import io.ktor.http.HttpStatusCode.Companion.NotFound
import io.ktor.http.HttpStatusCode.Companion.OK
import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.testing.*
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonObject
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Test
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class)
class TemplateRoutesTest {

    @Test
    fun `should return list of templates`() = testApplication {
        setupApplication()

        val client = setupClient()
        client.get("/template").apply {
            assertEquals(OK, status)
            // Fake template repository seeds itself with 1 template
            assertEquals(1, body<List<Template>>().size)
        }
    }

    @Test
    fun `should return template by ID`() = testApplication {
        setupApplication()

        val client = setupClient()
        client.get("/template/${Uuid.NIL}").apply {
            assertEquals(OK, status)
            assertNotNull(body<Template>())
        }
    }

    @Test
    fun `should create template`() = testApplication {
        setupApplication()

        val client = setupClient()
        val request = NewTemplate(
            name = "Data is not from before date",
            criterionType = CriterionType.VALID_INVALID,
            targetAspect = QualityAspect.TIMELINESS,
            evaluationMethod = EvaluationMethod(
                engine = Engine.JQ,
                variableSchema = buildJsonObject {
                    putJsonObject("properties") {
                        putJsonObject("date") {
                            put("type", "string")
                        }
                    }
                },
                implementationTemplate = ".timestamp >= {{ date }}"
            )
        )
        client.post("/template") {
            contentType(Application.Json)
            setBody(request)
        }.apply {
            val id = Uuid.parse(body<IDDTO>().id)
            assertEquals(Created, status)

            client.get("/template/${id}").apply {
                assertEquals(OK, status)

                val retrieved = body<Template>()
                assertEquals(id, retrieved.id)
                assertEquals(request.name, retrieved.name)
                assertEquals(request.criterionType, retrieved.criterionType)
                assertEquals(request.targetAspect, retrieved.targetAspect)
                assertEquals(request.evaluationMethod, retrieved.evaluationMethod)
            }

            client.get("/template").apply {
                assertEquals(OK, status)
                assertEquals(2, body<List<Template>>().size)
            }
        }
    }

    @Test
    fun `should update template`() = testApplication {
        setupApplication()

        val client = setupClient()
        // Adds description to the default seed template
        val patch = TemplatePatch(
            id = Uuid.NIL,
            description = "Ensures that the timestamp property of the data is less than or equal to the data parameter",
        )
        client.patch("/template/${patch.id}") {
            contentType(Application.Json)
            setBody(patch)
        }.apply {
            assertEquals(OK, status)

            val updatedTemplate = body<Template>()
            assertEquals(patch.id, updatedTemplate.id)
            assertEquals(patch.description, updatedTemplate.description)

            // Updated template is returned by GET
            client.get("/template/${patch.id}").apply {
                assertEquals(OK, status)

                val retrieved = body<Template>()
                assertEquals(patch.id, retrieved.id)
                assertEquals(patch.description, retrieved.description)
            }

            // No new template has been created
            client.get("/template").apply {
                assertEquals(OK, status)
                assertEquals(1, body<List<Template>>().size)
            }
        }
    }

    @Test
    fun `should remove template`() = testApplication {
        setupApplication()

        val client = setupClient()
        client.delete("/template/${Uuid.NIL}").apply {
            assertEquals(NoContent, status)

            // There are no more templates
            client.get("/template").apply {
                assertEquals(OK, status)
                assertEquals(0, body<List<Template>>().size)
            }
        }
    }

    @Test
    fun `should return 404 when template not found`() = testApplication {
        setupApplication()

        val patch = TemplatePatch(id = Uuid.NIL)

        val client = setupClient()
        val randomUUID = Uuid.random()
        client.get("/template/$randomUUID").apply {
            assertEquals(NotFound, status)
        }
        client.patch("/template/$randomUUID") {
            contentType(Application.Json)
            setBody(TemplatePatch(id = randomUUID))
        }.apply {
            assertEquals(NotFound, status)
        }
        client.delete("/template/$randomUUID").apply {
            assertEquals(NotFound, status)
        }
    }
}

private fun ApplicationTestBuilder.setupApplication() = application {
    testModule()
    templateRoutes()
}

private fun ApplicationTestBuilder.setupClient(): HttpClient = createClient {
    install(ContentNegotiation) { json() }
}