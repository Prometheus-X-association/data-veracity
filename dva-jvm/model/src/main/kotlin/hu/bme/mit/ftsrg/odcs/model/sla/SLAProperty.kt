package hu.bme.mit.ftsrg.odcs.model.sla

import kotlinx.serialization.Contextual
import kotlinx.serialization.Serializable

@Serializable
data class SLAProperty(
  val driver: String?,
  val element: String?,
  val property: String,
  val unit: String?,
  val value: @Contextual Any,
  val valueExt: @Contextual Any?,
)
