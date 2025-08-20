package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.resource.Templates
import hu.bme.mit.ftsrg.dva.dto.ErrorDTO
import hu.bme.mit.ftsrg.dva.dto.IDDTO
import hu.bme.mit.ftsrg.dva.vla.NewTemplate
import hu.bme.mit.ftsrg.dva.vla.TemplatePatch
import hu.bme.mit.ftsrg.dva.vla.TemplateRepository
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
import org.koin.ktor.ext.inject

fun Application.templateRoutes() {
    val repo: TemplateRepository by inject()

    routing {
        get<Templates> {
            call.respond(repo.allTemplates())
        }

        get<Templates.Id> { req ->
            val template = repo.templateById(req.id) ?: run {
                call.respond(NotFound, ErrorDTO(type = "NOT_FOUND", title = "Template not found"))
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
            call.respond(Created, IDDTO(template.id))
        }

        patch<Templates.Id> {
            val patch = call.receive<TemplatePatch>()
            val updatedTemplate = repo.patchTemplate(patch) ?: run {
                call.respond(
                    NotFound,
                    ErrorDTO(type = "NOT_FOUND", title = "Template not found")
                )
                return@patch
            }
            call.respond(updatedTemplate)
        }

        delete<Templates.Id> { req ->
            if (repo.removeTemplate(req.id)) {
                call.respond(NoContent)
            } else {
                call.respond(NotFound, ErrorDTO(type = "NOT_FOUND", title = "Template not found"))
            }
        }
    }
}