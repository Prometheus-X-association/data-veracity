package hu.bme.mit.ftsrg.dva.api.testutil

import hu.bme.mit.ftsrg.dva.api.error.addHandlers
import hu.bme.mit.ftsrg.dva.vla.FakeTemplateRepository
import hu.bme.mit.ftsrg.dva.vla.TemplateRepository
import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.application.*
import io.ktor.server.plugins.calllogging.*
import io.ktor.server.plugins.contentnegotiation.*
import io.ktor.server.plugins.statuspages.*
import io.ktor.server.resources.*
import kotlinx.serialization.json.Json
import org.koin.dsl.module
import org.koin.ktor.plugin.Koin
import org.slf4j.event.Level

fun Application.testModule() {
    val appModule = module { single<TemplateRepository> { FakeTemplateRepository() } }

    install(CallLogging) { level = Level.DEBUG }
    install(StatusPages) { addHandlers() }
    install(ContentNegotiation) { json(Json { explicitNulls = true }) }
    install(Resources)
    install(Koin) { modules(appModule) }
}