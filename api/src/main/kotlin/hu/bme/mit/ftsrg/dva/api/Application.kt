package hu.bme.mit.ftsrg.dva.api

import hu.bme.mit.ftsrg.dva.api.error.addHandlers
import hu.bme.mit.ftsrg.dva.api.route.aovRoutes
import hu.bme.mit.ftsrg.dva.api.route.docRoutes
import hu.bme.mit.ftsrg.dva.api.route.templateRoutes
import hu.bme.mit.ftsrg.dva.persistence.repository.AttestationRequestRepository
import hu.bme.mit.ftsrg.dva.persistence.repository.VLATemplateRepository
import hu.bme.mit.ftsrg.dva.persistence.repository.fake.FakeAttestationRequestRepository
import hu.bme.mit.ftsrg.dva.persistence.repository.fake.FakeVLATemplateRepository
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.application.*
import io.ktor.server.cio.*
import io.ktor.server.plugins.calllogging.*
import io.ktor.server.plugins.contentnegotiation.*
import io.ktor.server.plugins.statuspages.*
import io.ktor.server.request.*
import io.ktor.server.resources.*
import kotlinx.serialization.json.Json
import org.slf4j.event.Level

fun main(args: Array<String>): Unit = EngineMain.main(args)

fun Application.module() {
  val templateRepository = FakeVLATemplateRepository()
  val aovRequestRepository = FakeAttestationRequestRepository()

  installPlugins()
  addRoutes(
    templateRepository = templateRepository,
    aovRequestRepository = aovRequestRepository,
  )
}

fun Application.installPlugins() {
  install(CallLogging) {
    level = Level.DEBUG
    format { call ->
      val status: HttpStatusCode? = call.response.status()
      val method = call.request.httpMethod.value
      val path: String = call.request.path()
      val time: Long = call.processingTimeMillis()
      val size: String? = call.response.headers["Content-Length"]

      val sizeStr = size?.let { " with body of $it bytes" } ?: ""

      "$method $path -> $status in $time ms$sizeStr"
    }
  }

  install(StatusPages) { addHandlers() }

  install(ContentNegotiation) { json(Json { explicitNulls = true }) }

  install(Resources)
}

fun Application.addRoutes(
  templateRepository: VLATemplateRepository,
  aovRequestRepository: AttestationRequestRepository
) {
  docRoutes()
  templateRoutes(templateRepository)
  aovRoutes(aovRequestRepository)
}