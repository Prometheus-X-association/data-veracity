package hu.bme.mit.ftsrg.dva.api.resource

import io.ktor.resources.*

@Resource("/template")
class Templates {

  @Resource("{id}")
  class Id(val parent: Templates = Templates(), val id: String)
}