package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.deprecated.VLATemplateRepository
import hu.bme.mit.ftsrg.dva.api.error.NotFoundError
import hu.bme.mit.ftsrg.dva.api.error.UnimplementedError
import hu.bme.mit.ftsrg.dva.api.resource.Templates
import hu.bme.mit.ftsrg.dva.dto.IDDTO
import hu.bme.mit.ftsrg.dva.model.vla.VLATemplate
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
    val templates: List<VLATemplate> = repository.all()
    call.respond(templates)
  }

  /**
   * Create a new VLA template.
   */
  post<Templates> {
    val template: VLATemplate = call.receive()
    repository.add(template)
    call.response.status(HttpStatusCode.Created)
    call.respond(IDDTO(template.id))
  }

  /**
   * Get a VLA template by its ID.
   */
  get<Templates.Id> { template ->
    repository.byID(template.id)?.apply {
      call.respond(this)
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
    repository.remove(template.id)
    call.response.status(HttpStatusCode.OK)
  }
}