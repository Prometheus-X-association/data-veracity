package hu.bme.mit.ftsrg.dva.api.route

import com.rabbitmq.client.Connection
import com.rabbitmq.client.MessageProperties
import hu.bme.mit.ftsrg.connector.model.DataExchange
import hu.bme.mit.ftsrg.dva.api.resource.Attestations
import hu.bme.mit.ftsrg.dva.dto.ResultDTO
import hu.bme.mit.ftsrg.dva.persistence.repository.DataExchangeRepository
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
import kotlinx.serialization.json.encodeToJsonElement

fun Application.aovRoutes(rmqConnection: Connection, exchangeRepository: DataExchangeRepository) {
  routing {
    aovRoute(rmqConnection, exchangeRepository)
  }
}

fun Route.aovRoute(rmqConnection: Connection, exchangeRepository: DataExchangeRepository) {
  post<Attestations> {
    val request: DataExchange = call.receive()

    rmqConnection.confirmChannel {
      declareQueue(QueueSpecification("ATTESTATION_REQUESTS"))
      publish {
        publishWithConfirm(createMessage(Json.encodeToString(request)))
      }
    }

    exchangeRepository.add(request)

    call.respond(ResultDTO(Json.encodeToJsonElement("OK")))
  }

  /* TODO: Implement verification */
  post<Attestations.Verify> {
    val request: DataExchange = call.receive()
    exchangeRepository.add(request)
    call.respond(ResultDTO(Json.encodeToJsonElement("Unimplemented")))
  }
}

private fun createMessage(body: String): OutboundMessage =
  OutboundMessage(
    exchange = "",
    routingKey = "ATTESTATION_REQUESTS",
    properties = MessageProperties.PERSISTENT_BASIC,
    msg = body
  )