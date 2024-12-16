package hu.bme.mit.ftsrg.dva.api.testutil

import hu.bme.mit.ftsrg.dva.api.error.addHandlers
import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.application.*
import io.ktor.server.plugins.contentnegotiation.*
import io.ktor.server.plugins.statuspages.*
import io.ktor.server.resources.*
import kotlinx.serialization.json.Json

fun Application.testModule() {
  install(StatusPages) { addHandlers() }
  install(ContentNegotiation) { json(Json { explicitNulls = true }) }
  install(Resources)
}