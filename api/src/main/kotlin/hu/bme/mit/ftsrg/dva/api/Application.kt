package hu.bme.mit.ftsrg.dva.api

import hu.bme.mit.ftsrg.dva.api.route.docRoutes
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.cio.*
import io.ktor.server.plugins.calllogging.*
import io.ktor.server.request.*
import org.slf4j.event.Level

fun main(args: Array<String>): Unit = EngineMain.main(args)

fun Application.module() {
  install(CallLogging) {
    level = Level.DEBUG
    format { call ->
      val status: HttpStatusCode? = call.response.status()
      val method = call.request.httpMethod.value
      val path: String = call.request.path()
      val time: Long = call.processingTimeMillis()

      "$method $path -> $status in $time ms"
    }
  }


  docRoutes()
}
