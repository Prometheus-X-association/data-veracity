package hu.bme.mit.ftsrg.dva.api.testutil

import hu.bme.mit.ftsrg.dva.api.err.addHandlers
import hu.bme.mit.ftsrg.dva.vla.FakeTemplateRepo
import hu.bme.mit.ftsrg.dva.vla.FakeVLARepo
import hu.bme.mit.ftsrg.dva.vla.TemplateRepo
import hu.bme.mit.ftsrg.dva.vla.VLARepo
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
    val appModule = module {
        single<TemplateRepo> { FakeTemplateRepo() }
        single<VLARepo> { FakeVLARepo() }
    }

    install(CallLogging) { level = Level.DEBUG }
    install(StatusPages) { addHandlers() }
    install(ContentNegotiation) { json(Json { explicitNulls = true }) }
    install(Resources)
    install(Koin) { modules(appModule) }
}