package hu.bme.mit.ftsrg.dva.api

import hu.bme.mit.ftsrg.dva.api.route.docRoutes
import io.ktor.server.application.*
import io.ktor.server.cio.*

fun main(args: Array<String>): Unit = EngineMain.main(args)

fun Application.module() {
  docRoutes()
}
