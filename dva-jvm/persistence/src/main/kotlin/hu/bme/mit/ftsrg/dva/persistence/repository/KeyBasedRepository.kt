package hu.bme.mit.ftsrg.dva.persistence.repository

interface KeyBasedRepository<EntityType, KeyType> {
  fun all(): List<EntityType>
  fun byID(id: KeyType): EntityType?
  fun add(entity: EntityType)
  fun remove(id: KeyType)
}