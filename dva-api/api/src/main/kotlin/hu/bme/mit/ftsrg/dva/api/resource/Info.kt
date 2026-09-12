package hu.bme.mit.ftsrg.dva.api.resource

import io.ktor.resources.*

@Suppress("unused")
@Resource("/info")
class Info {

    @Resource("requests")
    class Requests(val parent: Info = Info())

    // TODO: Info endpoints for credential-related queries
}