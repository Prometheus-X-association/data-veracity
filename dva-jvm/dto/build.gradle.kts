plugins {
  id("buildlogic.kotlin-library-conventions")
  alias(libs.plugins.kotlin.serialization)
}

dependencies {
  implementation(libs.kotlinx.serialization.json)
  implementation(libs.bson)

  api(project(":model"))
}