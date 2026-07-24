package hu.bme.mit.ftsrg.dva.api.err

import io.ktor.http.*
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class)
class MissingVLAErr(val vlaID: Uuid) : APIErr(ErrType.NOT_FOUND, HttpStatusCode.NotFound, "VLA $vlaID not found")