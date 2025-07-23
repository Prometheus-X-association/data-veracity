package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.error.UnimplementedError
import hu.bme.mit.ftsrg.dva.api.resource.Templates
import io.ktor.server.application.*
import io.ktor.server.resources.*
import io.ktor.server.resources.patch
import io.ktor.server.resources.post
import io.ktor.server.routing.*

fun Application.templateRoutes() {
    routing {
        templateRoute()
    }
}

fun Route.templateRoute() {
    get<Templates> {
        throw UnimplementedError
    }

    post<Templates> {
        throw UnimplementedError
    }

    get<Templates.Id> {
        throw UnimplementedError
    }

    patch<Templates.Id> {
        throw UnimplementedError
    }

    delete<Templates.Id> {
        throw UnimplementedError
    }
}