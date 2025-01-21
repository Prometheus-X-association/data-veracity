package hu.bme.mit.ftsrg.dva.processing.aov

import com.rabbitmq.client.Connection
import com.rabbitmq.client.Delivery
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationRequestDTO
import hu.bme.mit.ftsrg.dva.model.aov.AttestationOfVeracity
import hu.bme.mit.ftsrg.vc.model.CredentialSubject
import hu.bme.mit.ftsrg.vc.model.VerifiableCredential
import io.github.oshai.kotlinlogging.KotlinLogging
import io.github.viartemev.rabbitmq.channel.channel
import io.github.viartemev.rabbitmq.channel.consume
import io.github.viartemev.rabbitmq.queue.QueueSpecification
import io.github.viartemev.rabbitmq.queue.declareQueue
import io.ktor.client.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.plugins.logging.*
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.serialization.json.Json
import java.time.ZonedDateTime
import java.util.*

private val logger = KotlinLogging.logger {}

suspend fun processAttestationRequests(rmqConnection: Connection) {
  rmqConnection.channel {
    declareQueue(QueueSpecification("ATTESTATION_REQUESTS"))
    consume("ATTESTATION_REQUESTS", 1) {
      consumeMessagesWithConfirm(::newRequestCallback)
    }
  }
}

suspend fun newRequestCallback(delivery: Delivery) {
  val request: AttestationRequestDTO = Json.decodeFromString(delivery.body.toString(Charsets.UTF_8))
  logger.info { "Received attestation request with ID ${request.id}" }

  val attestation = AttestationOfVeracity(
    aovID = UUID.randomUUID().toString(),
    contractId = UUID.randomUUID().toString(),
    evaluations = emptyList(),
    vc = VerifiableCredential(
      id = UUID.randomUUID().toString(),
      type = "VerfiableCredential",
      validFrom = ZonedDateTime.now(),
      subject = CredentialSubject(id = request.contract.dataProvider),
      issuer = request.attesterID,
    ),
  )

  HttpClient(CIO) {
    install(Logging)
    install(ContentNegotiation) { json() }
  }.use { client ->
    client.post(request.callbackURL) {
      contentType(ContentType.Application.Json)
      setBody(attestation)
    }
  }
}