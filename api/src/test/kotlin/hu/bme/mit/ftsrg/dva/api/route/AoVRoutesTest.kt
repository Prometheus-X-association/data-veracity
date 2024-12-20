package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.contractmanager.contract.model.Contract
import hu.bme.mit.ftsrg.contractmanager.contract.model.Negotiator
import hu.bme.mit.ftsrg.contractmanager.contract.model.Status
import hu.bme.mit.ftsrg.dva.api.testutil.testModule
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationRequestDTO
import hu.bme.mit.ftsrg.dva.persistence.repository.fake.FakeAttestationRequestRepository
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
import java.net.URI

/* TODO: These tests should not be coupled with FakeAttestationRequestRepository */
class AoVRoutesTest {

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
        purpose = emptyList(),
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
        )
      ),
      data = byteArrayOf(),
      callbackURL = URI("http://example.com/callback").toURL(),
    )

    client.post("/attestation") {
      contentType(ContentType.Application.Json)
      setBody(request)
    }.apply {
      Assertions.assertEquals(HttpStatusCode.OK, status)
    }
  }
}

private fun ApplicationTestBuilder.setupApplication() = application {
  testModule()
  aovRoutes(FakeAttestationRequestRepository())
}

private fun ApplicationTestBuilder.setupClient(): HttpClient = createClient {
  install(ContentNegotiation) { json() }
}

private val iriFactory = IRIFactory.iriImplementation()