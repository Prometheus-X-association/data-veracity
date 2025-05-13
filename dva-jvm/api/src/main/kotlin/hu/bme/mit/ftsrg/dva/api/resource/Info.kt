package hu.bme.mit.ftsrg.dva.api.resource

import io.ktor.resources.*

@Resource("/info")
class Info {

  @Resource("attestations")
  class Attestations(val parent: Info = Info())

  @Resource("verifications")
  class Verifications(val parent: Info = Info())
}