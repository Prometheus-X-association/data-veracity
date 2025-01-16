plugins {
  id("buildlogic.kotlin-library-conventions")
  alias(libs.plugins.kotlin.serialization)
}

dependencies {
  implementation(libs.bundles.ktor.client)
  implementation(libs.bundles.logging)
  implementation(libs.kotlinx.coroutines.core)
  implementation(libs.kotlinx.serialization.json)
  implementation(libs.rabbitmq.amqp.client)
  implementation(libs.rabbitmq.kotlin)
  implementation(project(":dto"))
}