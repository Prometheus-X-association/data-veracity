package hu.bme.mit.ftsrg.dva.api.resource

import io.ktor.resources.*

@Suppress("unused")
@Resource("/attestation")
class Attestations {

    @Resource("verify")
    class Verify(val parent: Attestations = Attestations())
}