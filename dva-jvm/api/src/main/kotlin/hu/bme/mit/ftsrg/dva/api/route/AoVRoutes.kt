package hu.bme.mit.ftsrg.dva.api.route

import com.rabbitmq.client.Connection
import com.rabbitmq.client.MessageProperties
import hu.bme.mit.ftsrg.dva.api.error.UnimplementedError
import hu.bme.mit.ftsrg.dva.api.resource.Attestations
import hu.bme.mit.ftsrg.dva.dto.IDDTO
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationRequestDTO
import hu.bme.mit.ftsrg.dva.model.DVARequestMongoDoc
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
import kotlinx.datetime.Clock
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.litote.kmongo.coroutine.CoroutineCollection
import org.slf4j.Logger
import org.slf4j.LoggerFactory
import java.util.*

fun Application.aovRoutes(rmqConnection: Connection, aovReqsColl: CoroutineCollection<DVARequestMongoDoc>) {
  routing {
    aovRoute(rmqConnection, aovReqsColl)
  }
}

fun Route.aovRoute(rmqConnection: Connection, aovReqsColl: CoroutineCollection<DVARequestMongoDoc>) {
  post<Attestations> {
    val request: AttestationRequestDTO = call.receive()

    val id = UUID.randomUUID().toString()
    val requestWithID: AttestationRequestDTO = request.copy(id = id)

    logReqToMongo(
      coll = aovReqsColl,
      req =
        DVARequestMongoDoc(
          type = "aov",
          requestID = requestWithID.id,
          vlaID = requestWithID.contract.vla.id,
          data = requestWithID.data,
          attesterID = requestWithID.attesterID,
          receivedDate = Clock.System.now(),
        )
    )

    rmqConnection.confirmChannel {
      declareQueue(QueueSpecification("ATTESTATION_REQUESTS"))
      publish {
        publishWithConfirm(createMessage(Json.encodeToString(requestWithID)))
      }
    }

    call.respond(IDDTO(id))
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

private suspend fun logReqToMongo(
  coll: CoroutineCollection<DVARequestMongoDoc>,
  req: DVARequestMongoDoc,
) {
  val logger: Logger = LoggerFactory.getLogger("AoVRoute")

  try {
    coll.insertOne(req)
    logger.info("Logged AoV request ${req.requestID} into MongoDB")
  } catch (e: Exception) {
    logger.error("Failed to insert AoV request ${req.requestID} into MongoBD due to error: ${e.message}", e)
  }
}