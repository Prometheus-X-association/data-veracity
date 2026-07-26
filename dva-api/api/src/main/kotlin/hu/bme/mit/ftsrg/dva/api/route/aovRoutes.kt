package hu.bme.mit.ftsrg.dva.api.route

import com.rabbitmq.client.Connection
import com.rabbitmq.client.MessageProperties
import hu.bme.mit.ftsrg.dva.api.resource.Attestations
import hu.bme.mit.ftsrg.dva.dto.IDDTO
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationRequestDTO
import hu.bme.mit.ftsrg.dva.log.*
import io.github.viartemev.rabbitmq.channel.confirmChannel
import io.github.viartemev.rabbitmq.channel.publish
import io.github.viartemev.rabbitmq.publisher.OutboundMessage
import io.github.viartemev.rabbitmq.queue.QueueSpecification
import io.github.viartemev.rabbitmq.queue.declareQueue
import io.ktor.http.*
import io.ktor.http.HttpStatusCode.Companion.Accepted
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.resources.post
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.koin.ktor.ext.inject
import java.util.*
import kotlin.time.Clock
import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalTime::class, ExperimentalUuidApi::class)
fun Application.aovRoutes() {
    val rmqConnection by inject<Connection>()
    val reqsRepo by inject<ReqestLogRepo>()

    routing {
        post<Attestations> {
            val request: AttestationRequestDTO = call.receive()

            val id = UUID.randomUUID().toString()
            val requestWithID: AttestationRequestDTO = request.copy(id = id)

            reqsRepo.add(
                RequestLogNew(
                    type = RequestType.ATTESTATION_REQUEST,
                    requestID = Uuid.parse(requestWithID.id!!),
                    exchangeID = requestWithID.exchangeID,
                    contractID = requestWithID.contract["id"].toString(),
                    vlaID = Uuid.parse(requestWithID.contract["vla"]?.jsonObject["id"]?.jsonPrimitive?.content!!),
                    data = requestWithID.data,
                    attesterID = requestWithID.attesterID,
                    receivedDate = Clock.System.now(),
                )
            )

            rmqConnection.confirmChannel {
                declareQueue(QueueSpecification("ATTESTATION_REQUESTS", durable = true))
                publish {
                    publishWithConfirm(createMessage(Json.encodeToString(requestWithID)))
                }
            }

            call.respond(status = Accepted, message = IDDTO(id))
        }

        post<Attestations.Verify> {
            // TODO: Needs reimplementation since removal of ACA-Py
            call.response.status(HttpStatusCode.NotAcceptable)
        }
    }
}

private fun createMessage(body: String): OutboundMessage =
    OutboundMessage(
        exchange = "",
        routingKey = "ATTESTATION_REQUESTS",
        properties = MessageProperties.PERSISTENT_BASIC,
        msg = body
    )