package hu.bme.mit.ftsrg.dva.api.error

import hu.bme.mit.ftsrg.dva.api.dto.ErrorDTO
import java.net.URI

enum class ErrorType(val uri: URI, val title: String) {
  ALREADY_EXISTS(URI("/errors/exists"), "Resource already exists"),
  NOT_FOUND(URI("/errors/not_found"), "Resource Not Found"),
  UNIMPLEMENTED(URI("/errors/unimplemented"), "Unimplemented feature"),
  UNKNOWN(URI("/errors/unknown"), "Unknown Error"),
}

fun errorDTO(type: ErrorType, init: ErrorDTO.() -> Unit = {}): ErrorDTO = ErrorDTO(type = type.uri.path, title = type.title).apply(init)