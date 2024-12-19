plugins {
  id("buildlogic.kotlin-library-conventions")
}

dependencies {
  implementation(libs.bundles.text.case.converter)
  implementation(libs.jena.iri)
  implementation(libs.kotlinx.serialization.json)
}