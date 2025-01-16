plugins {
    id("buildlogic.kotlin-application-conventions")
    alias(libs.plugins.ktor)
    alias(libs.plugins.kotlin.serialization)
}

dependencies {
    implementation(libs.bundles.ktor.server)
    implementation(libs.ktor.server.html.builder)
    implementation(libs.rabbitmq.amqp.client)
    implementation(libs.rabbitmq.kotlin)
    implementation(libs.slf4j.api)
    implementation(project(":dto"))
    implementation(project(":model"))
    implementation(project(":persistence"))

    runtimeOnly(libs.bundles.penna)

    testImplementation(libs.ktor.client.content.negotiation)
    testImplementation(libs.ktor.server.test.host)
    testImplementation(libs.rabbitmq.mock)
}

application {
    mainClass = "hu.bme.mit.ftsrg.dva.api.ApplicationKt"
}

tasks.withType<Test> {
    workingDir = layout.projectDirectory.dir("../").asFile
}