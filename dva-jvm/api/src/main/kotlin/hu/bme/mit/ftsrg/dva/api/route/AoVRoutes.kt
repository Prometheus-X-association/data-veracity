package hu.bme.mit.ftsrg.dva.api.route

import com.rabbitmq.client.Connection
import com.rabbitmq.client.MessageProperties
import hu.bme.mit.ftsrg.dva.api.error.UnimplementedError
import hu.bme.mit.ftsrg.dva.api.resource.Attestations
import hu.bme.mit.ftsrg.dva.dto.IDDTO
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationRequestDTO
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationVerificationRequestDTO
import io.github.viartemev.rabbitmq.channel.confirmChannel
import io.github.viartemev.rabbitmq.channel.publish
import io.github.viartemev.rabbitmq.publisher.OutboundMessage
import io.github.viartemev.rabbitmq.queue.QueueSpecification
import io.github.viartemev.rabbitmq.queue.declareQueue
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.resources.post
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.util.*

fun Application.aovRoutes(rmqConnection: Connection) {
  routing {
    aovRoute(rmqConnection)
  }
}

fun Route.aovRoute(rmqConnection: Connection) {
  post<Attestations> {
    val request: AttestationRequestDTO = call.receive()

    val id = UUID.randomUUID().toString()
    val requestWithID: AttestationRequestDTO = request.copy(id = id)

    rmqConnection.confirmChannel {
      declareQueue(QueueSpecification("ATTESTATION_REQUESTS"))
      publish {
        publishWithConfirm(createMessage(Json.encodeToString(requestWithID)))
      }
    }

    call.respond(IDDTO(id))
  }

  post<Attestations.Verify> {
    val request: AttestationVerificationRequestDTO = call.receive()

    val id = UUID.randomUUID().toString()
    val requestWithID: AttestationVerificationRequestDTO = request.copy(id = id)

    rmqConnection.confirmChannel {
      declareQueue(QueueSpecification("ATTESTATION_VERIFICATION_REQUESTS"))
      publish {
        publishWithConfirm(createMessage(Json.encodeToString(requestWithID)))
      }
    }

    call.respond(IDDTO(id))
  }
}

private fun createMessage(body: String): OutboundMessage =
  OutboundMessage(
    exchange = "",
    routingKey = "ATTESTATION_REQUESTS",
    properties = MessageProperties.PERSISTENT_BASIC,
    msg = body
  )