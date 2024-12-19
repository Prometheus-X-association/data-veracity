plugins {
    id("buildlogic.kotlin-application-conventions")
    alias(libs.plugins.ktor)
    alias(libs.plugins.kotlin.serialization)
}

dependencies {
    implementation(libs.bundles.ktor.server)
    implementation(libs.ktor.server.html.builder)
    implementation(libs.slf4j.api)
    implementation(project(":model"))
    implementation(project(":persistence"))

    runtimeOnly(libs.bundles.penna)

    testImplementation(libs.ktor.client.content.negotiation)
    testImplementation(libs.ktor.server.test.host)
}

application {
    mainClass = "hu.bme.mit.ftsrg.dva.api.ApplicationKt"
}

tasks.withType<Test> {
    workingDir = layout.projectDirectory.dir("../").asFile
}