package hu.bme.mit.ftsrg.dva.dto.aov

import kotlinx.serialization.json.JsonObject

@Suppress("unused")
interface ACAPyPresentationResponseDTO {
  val message: String
  val aov: JsonObject
}