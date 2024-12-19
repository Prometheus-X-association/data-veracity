package hu.bme.mit.ftsrg.dva.persistence.repository.fake

import hu.bme.mit.ftsrg.dva.dto.AttestationRequest
import hu.bme.mit.ftsrg.dva.persistence.repository.AttestationRequestRepository
import java.util.*

class FakeAttestationRequestRepository : AttestationRequestRepository {
  private val queue: Queue<AttestationRequest> = LinkedList()

  override fun all(): List<AttestationRequest> = queue.toList()

  override fun byID(id: String): AttestationRequest? = queue.find { it.id == id }

  override fun enqueue(entity: AttestationRequest): String {
    val id = UUID.randomUUID().toString()
    val requestWithID: AttestationRequest = entity.copy(id = id)
    queue.add(requestWithID)
    return id
  }

  override fun dequeue(): AttestationRequest? = queue.poll()
}