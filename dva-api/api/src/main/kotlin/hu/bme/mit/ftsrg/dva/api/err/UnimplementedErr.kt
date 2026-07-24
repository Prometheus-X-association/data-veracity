package hu.bme.mit.ftsrg.dva.api.err

import io.ktor.http.*

class UnimplementedErr : APIErr(ErrType.UNIMPLEMENTED, HttpStatusCode.NotImplemented, "This feature is not implemented")