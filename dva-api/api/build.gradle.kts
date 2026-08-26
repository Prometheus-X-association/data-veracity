plugins {
    id("buildlogic.kotlin-application-conventions")
    alias(libs.plugins.ktor)
    alias(libs.plugins.kotlin.serialization)
}

dependencies {
    implementation(libs.bundles.logging)
    implementation(libs.bundles.postgres)

    implementation(libs.bundles.ktor.client)
    implementation(libs.bundles.ktor.server)
    implementation(libs.ktor.server.html.builder)

    implementation(project.dependencies.platform(libs.koin.bom))
    implementation(libs.bundles.ktor.koin)

    implementation(libs.handlebars.java)
    implementation(libs.kotlinx.datetime)

    implementation(project(":model"))

    runtimeOnly(libs.logevents)

    testImplementation(libs.ktor.client.content.negotiation)
    testImplementation(libs.ktor.server.test.host)
}

application {
    mainClass = "hu.bme.mit.ftsrg.dva.api.ApplicationKt"
}

tasks.withType<Test> {
    testLogging {
        events("passed", "skipped", "failed")
    }
}
