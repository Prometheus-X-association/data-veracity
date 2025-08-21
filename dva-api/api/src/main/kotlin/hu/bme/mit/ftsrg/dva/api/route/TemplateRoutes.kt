package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.resource.Templates
import hu.bme.mit.ftsrg.dva.api.service.render
import hu.bme.mit.ftsrg.dva.dto.ErrorDTO
import hu.bme.mit.ftsrg.dva.dto.IDDTO
import hu.bme.mit.ftsrg.dva.vla.NewTemplate
import hu.bme.mit.ftsrg.dva.vla.TemplatePatch
import hu.bme.mit.ftsrg.dva.vla.TemplateRepository
import io.ktor.http.HttpStatusCode.Companion.BadRequest
import io.ktor.http.HttpStatusCode.Companion.Created
import io.ktor.http.HttpStatusCode.Companion.InternalServerError
import io.ktor.http.HttpStatusCode.Companion.NoContent
import io.ktor.http.HttpStatusCode.Companion.NotFound
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.resources.*
import io.ktor.server.resources.patch
import io.ktor.server.resources.post
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.json.JsonObject
import org.koin.ktor.ext.inject
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class)
fun Application.templateRoutes() {
    val repo by inject<TemplateRepository>()

    routing {
        get<Templates> {
            call.respond(repo.allTemplates())
        }

        get<Templates.Id> { req ->
            val template = repo.templateById(Uuid.parse(req.id)) ?: run {
                call.respond(NotFound)
                return@get
            }
            call.respond(template)
        }

        post<Templates> {
            val templateReq = call.receive<NewTemplate>()

            val template = repo.addTemplate(templateReq) ?: run {
                call.respond(InternalServerError, ErrorDTO(type = "UNKNOWN", title = "Failed to create template"))
                return@post
            }
            call.respond(Created, IDDTO(template.id.toString()))
        }

        patch<Templates.Id> { req ->
            val patch = call.receive<TemplatePatch>()
            if (Uuid.parse(req.id) != patch.id) {
                call.respond(
                    status = BadRequest,
                    ErrorDTO(type = "BAD_REQUEST", title = "ID path parameter does not match ID in body")
                )
            }
            val updatedTemplate = repo.patchTemplate(patch) ?: run {
                call.respond(NotFound)
                return@patch
            }
            call.respond(updatedTemplate)
        }

        delete<Templates.Id> { req ->
            if (repo.removeTemplate(Uuid.parse(req.id))) {
                call.respond(NoContent)
            } else {
                call.respond(NotFound)
            }
        }

        post<Templates.Id.Render> { req ->
            val template = repo.templateById(Uuid.parse(req.parent.id)) ?: run {
                call.respond(NotFound)
                return@post
            }
            val model = call.receive<JsonObject>()
            val renderedQuality = template.render(model) ?: run {
                call.respond(BadRequest, ErrorDTO(type = "BAD_REQUEST", title = "Failed to render template"))
            }
            call.respond(renderedQuality)
        }
    }
}