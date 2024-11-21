plugins {
    id("buildlogic.kotlin-application-conventions")
    alias(libs.plugins.ktor)
}

dependencies {
    implementation(libs.ktor.server.core)
    implementation(libs.ktor.server.cio)
    implementation(libs.slf4j.api)
    runtimeOnly(libs.penna.core)
    testImplementation(libs.ktor.server.test.host)
}

application {
    mainClass = "hu.bme.mit.ftsrg.dva.server.ServerKt"
}
