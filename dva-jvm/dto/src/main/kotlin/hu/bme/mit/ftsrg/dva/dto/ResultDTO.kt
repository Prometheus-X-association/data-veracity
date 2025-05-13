package hu.bme.mit.ftsrg.dva.dto

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement

@Serializable
data class ResultDTO(val result: JsonElement)