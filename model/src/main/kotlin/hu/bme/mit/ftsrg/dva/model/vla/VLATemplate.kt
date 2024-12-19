package hu.bme.mit.ftsrg.dva.model.vla

import kotlinx.serialization.Serializable

@Serializable
data class VLATemplate(val id: String, val objective: VeracityObjective)
