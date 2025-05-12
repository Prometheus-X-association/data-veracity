package hu.bme.mit.ftsrg.dva.api.route

import com.rabbitmq.client.Connection
import com.rabbitmq.client.MessageProperties
import hu.bme.mit.ftsrg.connector.model.DataExchange
import hu.bme.mit.ftsrg.dva.api.error.UnimplementedError
import hu.bme.mit.ftsrg.dva.api.resource.Attestations
import hu.bme.mit.ftsrg.dva.dto.SuccessDTO
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

fun Application.aovRoutes(rmqConnection: Connection) {
  routing {
    aovRoute(rmqConnection)
  }
}

fun Route.aovRoute(rmqConnection: Connection) {
  post<Attestations> {
    val request: DataExchange = call.receive()

    rmqConnection.confirmChannel {
      declareQueue(QueueSpecification("ATTESTATION_REQUESTS"))
      publish {
        publishWithConfirm(createMessage(Json.encodeToString(request)))
      }
    }

    call.respond(SuccessDTO("OK"))
  }

  /* TODO: Implement verification */
  post<Attestations.Verify> {
    throw UnimplementedError
  }
}

private fun createMessage(body: String): OutboundMessage =
  OutboundMessage(
    exchange = "",
    routingKey = "ATTESTATION_REQUESTS",
    properties = MessageProperties.PERSISTENT_BASIC,
    msg = body
  )