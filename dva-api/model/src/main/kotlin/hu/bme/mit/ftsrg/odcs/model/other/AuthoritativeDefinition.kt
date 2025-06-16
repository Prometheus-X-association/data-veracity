@file:UseSerializers(URLSerializer::class)

package hu.bme.mit.ftsrg.odcs.model.other

import hu.bme.mit.ftsrg.serialization.java.URLSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import java.net.URL

@Serializable
data class AuthoritativeDefinition(val url: URL, val type: String)