package hu.bme.mit.ftsrg.dva.persistence.repository.fake

import hu.bme.mit.ftsrg.dva.dto.aov.AttestationRequestDTO
import hu.bme.mit.ftsrg.dva.persistence.repository.AttestationRequestRepository
import java.util.*

class FakeAttestationRequestRepository : AttestationRequestRepository {
  private val queue: Queue<AttestationRequestDTO> = LinkedList()

  override fun all(): List<AttestationRequestDTO> = queue.toList()

  override fun byID(id: String): AttestationRequestDTO? = queue.find { it.id == id }

  override fun enqueue(entity: AttestationRequestDTO): String {
    val id = UUID.randomUUID().toString()
    val requestWithID: AttestationRequestDTO = entity.copy(id = id)
    queue.add(requestWithID)
    return id
  }

  override fun dequeue(): AttestationRequestDTO? = queue.poll()
}