package hu.bme.mit.ftsrg.dva.api.route

import com.rabbitmq.client.ConnectionFactory
import hu.bme.mit.ftsrg.contractmanager.contract.model.Contract
import hu.bme.mit.ftsrg.contractmanager.contract.model.Negotiator
import hu.bme.mit.ftsrg.contractmanager.contract.model.Purpose
import hu.bme.mit.ftsrg.contractmanager.contract.model.Status
import hu.bme.mit.ftsrg.dva.api.testutil.testModule
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationRequestDTO
import hu.bme.mit.ftsrg.odcs.model.fundamentals.APIVersion
import hu.bme.mit.ftsrg.odcs.model.fundamentals.FileKind
import hu.bme.mit.ftsrg.odcs.model.quality.DataQuality
import hu.bme.mit.ftsrg.odcs.model.quality.DataQualityCustom
import hu.bme.mit.ftsrg.odcs.model.quality.DataQualityType
import hu.bme.mit.ftsrg.odcs.model.schema.LogicalType
import hu.bme.mit.ftsrg.odcs.model.schema.SchemaElement
import hu.bme.mit.ftsrg.odcs.model.schema.SchemaObject
import hu.bme.mit.ftsrg.odcs.model.schema.SchemaProperty
import hu.bme.mit.ftsrg.odrl.model.asset.Asset
import hu.bme.mit.ftsrg.odrl.model.policy.Policy
import hu.bme.mit.ftsrg.odrl.model.rule.Action
import hu.bme.mit.ftsrg.odrl.model.rule.Permission
import hu.bme.mit.ftsrg.odrl.model.rule.Rule
import io.ktor.client.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.testing.*
import org.apache.jena.iri.IRIFactory
import org.junit.jupiter.api.Assertions
import org.junit.jupiter.api.Test
import org.testcontainers.containers.RabbitMQContainer
import org.testcontainers.junit.jupiter.Container
import org.testcontainers.junit.jupiter.Testcontainers
import java.net.URI
import java.util.*
import hu.bme.mit.ftsrg.odcs.model.Contract as ODCSContract

/* TODO: These tests should not be coupled with FakeAttestationRequestRepository */
@Testcontainers
class AoVRoutesTest {

  @Container
  val rmqContainer: RabbitMQContainer = RabbitMQContainer("rabbitmq").withExposedPorts(5672)

  @Test
  fun `should create attestation request`() = testApplication {
    setupApplication()
    val client = setupClient()

    val request = AttestationRequestDTO(
      attesterID = "attester-0000",
      contract = Contract(
        dataProvider = "/catalog/participants/provider-test-id",
        dataConsumer = "/catalog/participants/consumer-test-did",
        serviceOffering = "/catalog/serviceofferings/serviceoffering-test-did",
        purpose = listOf(
          Purpose(
            purpose = "/catalog/serviceofferings",
            piiCategory = emptyList(),
          ),
        ),
        negotiators = listOf(
          Negotiator("/catalog/participants/provider-test-id"),
          Negotiator("/catalog/participants/consumer-test-did"),
        ),
        status = Status.PENDING,
        policy = listOf(
          Policy(
            uid = iriFactory.create("/policy/policy-0-uid"),
            permission = listOf(
              Permission(
                target = Asset(uid = iriFactory.create("/target/3f8d1b0e-8e2e-4b69-9b1f-089fe2f3e9d7")),
                rule = Rule(action = Action.USE),
              )
            ),
          )
        ),
        vla = ODCSContract(
          version = "1.0.0",
          kind = FileKind.DATA_CONTRACT,
          id = UUID.randomUUID().toString(),
          status = "active",
          name = "test",
          dataProduct = "test",
          apiVersion = APIVersion.V3_0_1,
          schema = listOf(
            SchemaObject(
              schemaElement = SchemaElement(name = "xapi_statement"),
              logicalType = LogicalType.OBJECT,
              properties = listOf(
                SchemaProperty(
                  schemaElement = SchemaElement(name = "id"),
                  logicalType = LogicalType.STRING,
                ),
                SchemaProperty(
                  schemaElement = SchemaElement(name = "actor"),
                  logicalType = LogicalType.OBJECT,
                  required = true,
                ),
                SchemaProperty(
                  schemaElement = SchemaElement(name = "verb"),
                  logicalType = LogicalType.OBJECT,
                  required = true,
                ),
                SchemaProperty(
                  schemaElement = SchemaElement(name = "object"),
                  logicalType = LogicalType.OBJECT,
                  required = true,
                ),
                SchemaProperty(
                  schemaElement = SchemaElement(name = "result"),
                  logicalType = LogicalType.OBJECT,
                ),
                SchemaProperty(
                  schemaElement = SchemaElement(name = "context"),
                  logicalType = LogicalType.OBJECT,
                ),
                SchemaProperty(
                  schemaElement = SchemaElement(name = "timestamp"),
                  logicalType = LogicalType.STRING,
                ),
                SchemaProperty(
                  schemaElement = SchemaElement(name = "stored"),
                  logicalType = LogicalType.STRING,
                ),
                SchemaProperty(
                  schemaElement = SchemaElement(name = "version"),
                  logicalType = LogicalType.STRING,
                ),
              ),
              quality = listOf(
                DataQualityCustom(
                  dataQuality = DataQuality(type = DataQualityType.CUSTOM),
                  engine = "greatExpectations",
                  implementation = """
                        type: ExpectColumnValuesToBeBetween
                        kwargs:
                          column: timestamp
                          min_value: '2025-01-01T00:00:00Z'
                          max_value: '2026-01-01T00:00:00Z'
                      """.trimIndent()
                )
              )
            )
          )
        ),
      ),
      data = """
        {
          "actor": {
            "name": "Jean Dupont",
            "mbox": "mailto:jeandupont@example.com"
          },
          "verb": {
            "id": "http://adlnet.gov/expapi/verbs/interacted",
            "display": {
              "en-US": "interacted"
            }
          },
          "object": {
            "id": "https://navy.mil/netc/xapi/activities/simulations/b9e16535-4fc9-4c66-ac87-3ad7ce515f5c/events/0221144",
            "definition": {
              "name": {
                "en-US": "Event in Simulator"
              },
              "description": {
                "en-US": "You're wearing all your PPE"
              },
              "type": "http://adlnet.gov/expapi/activities/interaction"
            }
          },
          "context": {
            "registration": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "extensions": {
              "https://w3id.org/xapi/cmi5/context/extensions/sessionid": "moodle-session-12345"
            }
          },
          "result": {
              "success":true,
              "extensions": {
              "http://id.tincanapi.com/extension/severity": "info"
            }
          },
          "timestamp": "2024-03-16T30:25:00Z"
        }
      """.trimIndent().toByteArray(charset = Charsets.UTF_8),
      callbackURL = URI("http://example.com/callback").toURL(),
      mapping = mapOf(
        "$.actor.name" to "actor",
        "$.verb.id" to "verb",
        "$.object.id" to "object",
        "$.timestamp" to "timestamp"
      ),
    )
    client.post("/attestation") {
      contentType(ContentType.Application.Json)
      setBody(request)
    }.apply {
      Assertions.assertEquals(HttpStatusCode.OK, status)
    }
  }

  private fun ApplicationTestBuilder.setupApplication() = application {
    val rmqConnectionFactory = ConnectionFactory().apply {
      host = rmqContainer.host
      port = rmqContainer.firstMappedPort
    }

    testModule()
    aovRoutes(rmqConnection = rmqConnectionFactory.newConnection())
  }

  private fun ApplicationTestBuilder.setupClient(): HttpClient = createClient {
    install(ContentNegotiation) { json() }
  }

  private val iriFactory = IRIFactory.iriImplementation()
}
