package hu.bme.mit.ftsrg.dva.api.resource

import io.ktor.resources.*

@Resource("/attestation")
class Attestations {

  @Resource("verify")
  class Verify(val parent: Attestations = Attestations())
}