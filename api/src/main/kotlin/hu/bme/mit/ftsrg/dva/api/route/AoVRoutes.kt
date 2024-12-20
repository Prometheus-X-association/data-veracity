package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.error.UnimplementedError
import hu.bme.mit.ftsrg.dva.api.resource.Attestations
import hu.bme.mit.ftsrg.dva.dto.IDDTO
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationRequestDTO
import hu.bme.mit.ftsrg.dva.persistence.repository.AttestationRequestRepository
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.resources.*
import io.ktor.server.resources.post
import io.ktor.server.response.*
import io.ktor.server.routing.*

fun Application.aovRoutes(repository: AttestationRequestRepository) {
  routing {
    aovRoute(repository)
  }
}

fun Route.aovRoute(repository: AttestationRequestRepository) {
  get<Attestations> {
    call.respondText("OK")
  }

  post<Attestations> {
    val request: AttestationRequestDTO = call.receive()
    val id: String = repository.enqueue(request)
    call.respond(IDDTO(id))
  }

  /* TODO: Implement verification */
  post<Attestations.Verify> {
    throw UnimplementedError
  }
}