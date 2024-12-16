package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.error.NotFoundError
import hu.bme.mit.ftsrg.dva.api.error.UnimplementedError
import hu.bme.mit.ftsrg.dva.api.resource.Templates
import hu.bme.mit.ftsrg.dva.dto.generic.IDDTO
import hu.bme.mit.ftsrg.dva.dto.vla.VLATemplateDTO
import hu.bme.mit.ftsrg.dva.persistence.repository.VLATemplateRepository
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.resources.*
import io.ktor.server.resources.patch
import io.ktor.server.resources.post
import io.ktor.server.response.*
import io.ktor.server.routing.*

fun Application.templateRoutes(repository: VLATemplateRepository) {
  routing {
    templateRoute(repository)
  }
}

fun Route.templateRoute(repository: VLATemplateRepository) {
  /**
   * Get all VLA templates.
   */
  get<Templates> {
    val templates = repository.allTemplates()
    val dtos = templates.map(VLATemplateDTO::fromBO)
    call.respond(dtos)
  }

  /**
   * Create a new VLA template.
   */
  post<Templates> {
    val dto: VLATemplateDTO = call.receive()
    repository.addTemplate(dto.toBO())
    call.respond(IDDTO(dto.id))
  }

  /**
   * Get a VLA template by its ID.
   */
  get<Templates.Id> { template ->
    repository.templateById(template.id)?.apply {
      call.respond(VLATemplateDTO.fromBO(this))
    } ?: throw NotFoundError("Template with id ${template.id} not found")
  }

  /* TODO: implement */
  patch<Templates.Id> {
    throw UnimplementedError
  }

  /**
   * Delete a VLA template by its ID.
   */
  delete<Templates.Id> { template ->
    repository.removeTemplate(template.id)
    call.response.status(HttpStatusCode.OK)
  }
}