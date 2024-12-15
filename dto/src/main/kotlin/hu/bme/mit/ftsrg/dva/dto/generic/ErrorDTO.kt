package hu.bme.mit.ftsrg.dva.dto.generic

import kotlinx.serialization.Serializable

/**
 * An RFC 7807 problem detail response DTO.
 */
@Serializable
data class ErrorDTO(
  var type: String? = null,
  var title: String? = null,
  var detail: String? = null,
  var instance: String? = null
)

fun errorDTO(init: ErrorDTO.() -> Unit): ErrorDTO = ErrorDTO().apply(init)