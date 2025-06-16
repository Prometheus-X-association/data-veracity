plugins {
  id("buildlogic.kotlin-library-conventions")
  alias(libs.plugins.kotlin.serialization)
}

dependencies {
  api(libs.jena.iri)
  implementation(libs.bundles.text.case.converter)
  implementation(libs.kasechange)
  implementation(libs.kotlinx.datetime)
  implementation(libs.kotlinx.serialization.json)
}