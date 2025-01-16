package hu.bme.mit.ftsrg.dva.persistence.repository

interface QueueRepository<EntityType, KeyType> {
  fun all(): List<EntityType>
  fun byID(id: KeyType): EntityType?
  fun enqueue(entity: EntityType): KeyType
  fun dequeue(): EntityType?
}