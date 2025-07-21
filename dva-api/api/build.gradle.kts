plugins {
  id("buildlogic.kotlin-application-conventions")
  alias(libs.plugins.ktor)
  alias(libs.plugins.kotlin.serialization)
}

dependencies {
  implementation(libs.bundles.ktor.server)
  implementation(libs.bundles.ktor.client)
  implementation(libs.bundles.logging)
  implementation(libs.bundles.mongo)
  implementation(libs.kotlinx.datetime)
  implementation(libs.ktor.server.html.builder)
  implementation(libs.rabbitmq.amqp.client)
  implementation(libs.rabbitmq.kotlin)
  implementation(libs.slf4j.api)
  implementation(project(":model"))

  runtimeOnly(libs.logevents)

  testImplementation(libs.bundles.testcontainers.mongodb)
  testImplementation(libs.bundles.testcontainers.rabbitmq)
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