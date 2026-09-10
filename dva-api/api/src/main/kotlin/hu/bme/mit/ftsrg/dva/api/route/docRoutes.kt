package hu.bme.mit.ftsrg.dva.api.route

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.html.*
import io.ktor.server.plugins.swagger.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.html.*
import java.io.File

/**
 * Names of the documents that may be served next to the OpenAPI file.
 *
 * Deliberately narrow: no dots in the stem and no separators, so no request can escape the
 * spec directory.
 */
private val SPEC_SIBLING_NAME = Regex("""[A-Za-z0-9_-]+\.yaml""")

private val YAML = ContentType.parse("application/yaml")

fun Application.docRoutes(openapiPath: String) {
    val specDir: File = File(openapiPath).canonicalFile.parentFile

    routing {
        get("/") {
            val name = "DVA"
            call.respondHtml(HttpStatusCode.OK) {
                head {
                    title {
                        +name
                    }
                }
                body {
                    h1 {
                        +"Welcome to the $name web UI"
                    }
                    p {
                        +"Click "
                        a(href = "/swagger") {
                            +"here"
                        }
                        +" to see the API documentation and test the service."
                    }
                }
            }
        }
        swaggerUI("swagger", swaggerFile = openapiPath)

        /*
         * Swagger UI resolves a relative `$ref` in the spec (eg `./components.yaml`) against the
         * URL the spec itself was loaded from, ie `/swagger/<file>`.  The swaggerUI plugin only
         * serves that one file, so the documents it references have to be served here; a constant
         * path segment outranks this parameterised one, so the spec itself still goes to the
         * plugin.
         */
        get("/swagger/{fileName}") {
            val name: String = call.parameters["fileName"].orEmpty()
            val file: File = File(specDir, name).canonicalFile
            if (!SPEC_SIBLING_NAME.matches(name) || file.parentFile != specDir || !file.isFile) {
                call.respond(HttpStatusCode.NotFound)
                return@get
            }
            call.respondText(file.readText(), YAML)
        }
    }
}
