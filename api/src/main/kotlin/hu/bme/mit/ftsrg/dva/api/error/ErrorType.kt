package hu.bme.mit.ftsrg.dva.api.error

import hu.bme.mit.ftsrg.dva.dto.generic.ErrorDTO
import java.net.URI

enum class ErrorType(val uri: URI, val title: String) {
  NOT_FOUND(URI("/errors/not_found"), "Resource Not Found"),
  UNKNOWN(URI("/errors/unknown"), "Unknown Error"),
}

fun errorDTO(type: ErrorType, init: ErrorDTO.() -> Unit = {}): ErrorDTO = ErrorDTO(type = type.uri.path, title = type.title).apply(init)