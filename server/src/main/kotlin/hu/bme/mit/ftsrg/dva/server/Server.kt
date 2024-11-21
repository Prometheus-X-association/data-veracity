package hu.bme.mit.ftsrg.dva.server

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.cio.*
import io.ktor.server.html.*
import io.ktor.server.plugins.swagger.*
import io.ktor.server.routing.*
import kotlinx.html.*

fun main(args: Array<String>): Unit = EngineMain.main(args)

fun Application.module() {
  routing {
    swaggerRoute()
    rootRoute()
  }
}

fun Route.swaggerRoute() {
  swaggerUI("swagger", swaggerFile = "spec/openapi.yaml")
}

fun Route.rootRoute() {
  get("/") {
    val name = "DVA"
    call.respondHtml(HttpStatusCode.OK) {
      head {
        title {
          +name
        }
      }
      body {
        h1 {
          +"Welcome to the $name web UI"
        }
        p {
          +"Click "
          a(href = "/swagger") {
            +"here"
          }
          +" to see the API documentation and test the service."
        }
      }
    }
  }
}