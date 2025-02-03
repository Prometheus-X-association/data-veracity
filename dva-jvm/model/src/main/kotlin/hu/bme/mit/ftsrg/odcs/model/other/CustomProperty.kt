package hu.bme.mit.ftsrg.odcs.model.other

import kotlinx.serialization.Contextual
import kotlinx.serialization.Serializable

@Serializable
data class CustomProperty(val property: String, @Contextual val value: Any)
