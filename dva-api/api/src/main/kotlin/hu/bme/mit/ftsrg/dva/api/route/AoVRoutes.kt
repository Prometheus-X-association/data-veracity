package hu.bme.mit.ftsrg.dva.api.route

import com.mongodb.client.model.Filters
import com.mongodb.client.model.Updates
import com.rabbitmq.client.Connection
import com.rabbitmq.client.MessageProperties
import hu.bme.mit.ftsrg.dva.api.resource.Attestations
import hu.bme.mit.ftsrg.dva.dto.IDDTO
import hu.bme.mit.ftsrg.dva.dto.aov.ACAPyPresentationRequestDTO
import hu.bme.mit.ftsrg.dva.dto.aov.ACAPyPresentationResponseDTO
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationRequestDTO
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationVerificationRequestDTO
import hu.bme.mit.ftsrg.dva.model.DVARequestMongoDoc
import hu.bme.mit.ftsrg.dva.model.DVAVerificationRequestMongoDoc
import io.github.viartemev.rabbitmq.channel.confirmChannel
import io.github.viartemev.rabbitmq.channel.publish
import io.github.viartemev.rabbitmq.publisher.OutboundMessage
import io.github.viartemev.rabbitmq.queue.QueueSpecification
import io.github.viartemev.rabbitmq.queue.declareQueue
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.resources.post
import io.ktor.server.response.*
import io.ktor.server.routing.*
import jdk.internal.vm.ScopedValueContainer.call
import kotlinx.datetime.Clock
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.litote.kmongo.coroutine.CoroutineCollection
import org.litote.kmongo.coroutine.CoroutineDatabase
import org.slf4j.Logger
import org.slf4j.LoggerFactory
import java.util.*
import kotlin.contracts.contract

fun Application.aovRoutes(rmqConnection: Connection, mongoDB: CoroutineDatabase, httpClient: HttpClient) {
  routing {
    aovRoute(rmqConnection, mongoDB, httpClient)
  }
}

fun Route.aovRoute(rmqConnection: Connection, mongoDB: CoroutineDatabase, httpClient: HttpClient) {
  val reqColl: CoroutineCollection<DVARequestMongoDoc> =
    mongoDB.getCollection(environment.config.property("mongodb.collections.aovRequests").getString())
  val verifReqColl: CoroutineCollection<DVAVerificationRequestMongoDoc> =
    mongoDB.getCollection(environment.config.property("mongodb.collections.aovVerificationRequests").getString())

  post<Attestations> {
    val request: AttestationRequestDTO = call.receive()

    val id = UUID.randomUUID().toString()
    val requestWithID: AttestationRequestDTO = request.copy(id = id)

    logToMongo(
      coll = reqColl,
      req =
        DVARequestMongoDoc(
          type = "aov",
          requestID = requestWithID.id,
          exchangeID = requestWithID.exchangeID,
          contractID = requestWithID.contract.id,
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

    call.respond(status = HttpStatusCode.Created, message = IDDTO(id))
  }

  post<Attestations.Verify> {
    val request: AttestationVerificationRequestDTO = call.receive()

    val id = UUID.randomUUID().toString()
    val requestWithID: AttestationVerificationRequestDTO = request.copy(id = id)

    logToMongo(
      coll = verifReqColl,
      req = DVAVerificationRequestMongoDoc(
        requestID = requestWithID.id,
        exchangeID = requestWithID.exchangeID,
        contractID = requestWithID.contractID,
        attesterAgentURL = requestWithID.attesterAgentURL,
        attesterAgentLabel = requestWithID.attesterAgentLabel,
        requestedAt = Clock.System.now(),
      )
    )

    val resp: HttpResponse =
      httpClient.post("${environment.config.property("acaPyAgent.url").getString()}/request_presentation_from_peer") {
        contentType(ContentType.Application.Json)
        setBody(
          ACAPyPresentationRequestDTO(
            dataExchangeId = requestWithID.exchangeID,
            attesterAgentURL = requestWithID.attesterAgentURL,
            attesterLabel = requestWithID.attesterAgentLabel
          )
        )
      }
    val acaPyResp: ACAPyPresentationResponseDTO = resp.body()

    verifReqColl.updateOne(
      filter = Filters.eq(DVAVerificationRequestMongoDoc::requestID.name, requestWithID.id),
      update = Updates.set(DVAVerificationRequestMongoDoc::presentationRequestData.name, acaPyResp.aov),
    )

    call.respond(status = resp.status, message = acaPyResp)
  }
}

private fun createMessage(body: String): OutboundMessage =
  OutboundMessage(
    exchange = "",
    routingKey = "ATTESTATION_REQUESTS",
    properties = MessageProperties.PERSISTENT_BASIC,
    msg = body
  )

private suspend fun <T : Any> logToMongo(coll: CoroutineCollection<T>, req: T) {
  val logger: Logger = LoggerFactory.getLogger("AoVRoute")

  try {
    coll.insertOne(req)
    logger.info("Logged document $req into MongoDB")
  } catch (e: Exception) {
    logger.error("Failed to insert document $req into MongoBD due to error: ${e.message}", e)
  }

}