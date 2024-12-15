plugins {
    id("buildlogic.kotlin-application-conventions")
    alias(libs.plugins.ktor)
}

dependencies {
    implementation(libs.bundles.ktor.server)
    implementation(libs.ktor.server.html.builder)
    implementation(libs.slf4j.api)
    runtimeOnly(libs.penna.core)
    testImplementation(libs.ktor.server.test.host)
}

application {
    mainClass = "hu.bme.mit.ftsrg.dva.server.ServerKt"
}

tasks.withType<Test> {
    workingDir = layout.projectDirectory.dir("../").asFile
}