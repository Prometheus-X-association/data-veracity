package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.resource.Info
import hu.bme.mit.ftsrg.dva.persistence.repository.DataExchangeRepository
import io.ktor.server.application.*
import io.ktor.server.resources.*
import io.ktor.server.response.*
import io.ktor.server.routing.*

fun Application.infoRoutes(exchangeRepository: DataExchangeRepository) {
  routing {
    infoRoute(exchangeRepository)
  }
}

fun Route.infoRoute(exchangeRepository: DataExchangeRepository) {
  get<Info.Attestations> {
    call.respond(exchangeRepository.all())
  }

  get<Info.Verifications> {
    call.respond(exchangeRepository.all())
  }
}