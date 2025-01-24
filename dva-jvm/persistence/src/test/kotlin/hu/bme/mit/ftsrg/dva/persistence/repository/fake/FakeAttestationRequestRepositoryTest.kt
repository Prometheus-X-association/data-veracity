package hu.bme.mit.ftsrg.dva.persistence.repository.fake

import hu.bme.mit.ftsrg.contractmanager.contract.model.Contract
import hu.bme.mit.ftsrg.contractmanager.contract.model.Negotiator
import hu.bme.mit.ftsrg.contractmanager.contract.model.Status
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationRequestDTO
import hu.bme.mit.ftsrg.dva.model.vla.*
import hu.bme.mit.ftsrg.odrl.model.asset.Asset
import hu.bme.mit.ftsrg.odrl.model.policy.Policy
import hu.bme.mit.ftsrg.odrl.model.rule.Action
import hu.bme.mit.ftsrg.odrl.model.rule.Permission
import hu.bme.mit.ftsrg.odrl.model.rule.Rule
import org.apache.jena.iri.IRIFactory
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import java.net.URI

class FakeAttestationRequestRepositoryTest {

  private lateinit var repository: FakeAttestationRequestRepository

  private val testRequest = AttestationRequestDTO(
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
          uid = iriFactory.create("policy-0-uid"),
          permission = listOf(
            Permission(
              target = Asset(uid = iriFactory.create("/target/3f8d1b0e-8e2e-4b69-9b1f-089fe2f3e9d7")),
              rule = Rule(action = Action.USE),
            )
          ),
        )
      ),
      vla = listOf(
        VLATemplate(
          id = "template-0001",
          objective = VeracityObjective(
            evaluationScheme = EvaluationScheme(
              evaluationMethod = "syntax_check",
              criterionType = CriterionType.VALID_INVALID,
            ),
            targetAspect = QualityAspect.SYNTAX,
          ),
        )
      ),
    ),
    data = byteArrayOf(),
    callbackURL = URI("http://example.com/callback").toURL(),
  )

  @BeforeEach
  fun setup() {
    repository = FakeAttestationRequestRepository()
  }

  @Test
  fun `should initialize to empty`() {
    assertTrue(repository.all().isEmpty())
  }

  @Test
  fun `should enqueue new attestation request`() {
    val id = repository.enqueue(testRequest)
    val retrieved: AttestationRequestDTO? = repository.byID(id)
    assertEquals(testRequest.copy(id = id), retrieved)
  }

  @Test
  fun `should return null when attempting to get request with nonexistent ID`() {
    assertNull(repository.byID("non-existing"))
  }

  @Test
  fun `should dequeue enqueued requests`() {
    val id = repository.enqueue(testRequest)
    val retrieved: AttestationRequestDTO? = repository.dequeue()
    assertEquals(testRequest.copy(id = id), retrieved)
    assertTrue(repository.all().isEmpty())
  }

  @Test
  fun `should return null when dequeueing from empty request queue`() {
    assertNull(repository.dequeue())
  }
}

private val iriFactory = IRIFactory.iriImplementation()