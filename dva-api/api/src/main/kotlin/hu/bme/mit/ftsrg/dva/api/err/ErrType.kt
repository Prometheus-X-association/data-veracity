package hu.bme.mit.ftsrg.dva.api.err

import hu.bme.mit.ftsrg.dva.dto.api.ErrDTO
import java.net.URI

enum class ErrType(val uri: URI, val title: String) {
    ALREADY_EXISTS(URI("/errors/exists"), "Resource already exists"),
    NOT_FOUND(URI("/errors/not_found"), "Resource Not Found"),
    BAD_REQUEST(URI("/errors/bad_request"), "Malformed request"),
    UNSUPPORTED_MEDIA_TYPE(URI("/errors/unsupported_media_type"), "Unsupported media type"),
    BAD_GATEWAY(URI("/errors/bad_gateway"), "Upstream service error"),
    UNIMPLEMENTED(URI("/errors/unimplemented"), "Unimplemented feature"),
    UNKNOWN(URI("/errors/unknown"), "Unknown Error"),
}

fun errDTO(type: ErrType, init: ErrDTO.() -> Unit = {}): ErrDTO =
    ErrDTO(type = type.uri.path, title = type.title).apply(init)