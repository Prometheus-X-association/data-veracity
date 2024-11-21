package hu.bme.mit.ftsrg.dva.server

import io.ktor.server.application.*
import io.ktor.server.cio.*
import io.ktor.server.response.*
import io.ktor.server.routing.*

fun main(args: Array<String>): Unit = EngineMain.main(args)

fun Application.module() {
  routing {
    get("/") {
      call.respondText("Hello World!")
    }
  }
}