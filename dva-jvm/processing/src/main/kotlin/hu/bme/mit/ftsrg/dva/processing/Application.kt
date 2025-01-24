package hu.bme.mit.ftsrg.dva.processing

import com.rabbitmq.client.Connection
import com.rabbitmq.client.ConnectionFactory
import hu.bme.mit.ftsrg.dva.processing.aov.processAttestationRequests
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

fun main(): Unit = runBlocking {
  val connectionFactory = ConnectionFactory().apply {
    host = System.getenv("DVA_RABBITMQ_HOST") ?: "localhost"
  }

  startProcessors(connectionFactory.newConnection())
}

suspend fun startProcessors(rmqConnection: Connection) = coroutineScope {
  launch {
    processAttestationRequests(rmqConnection)
  }
}

