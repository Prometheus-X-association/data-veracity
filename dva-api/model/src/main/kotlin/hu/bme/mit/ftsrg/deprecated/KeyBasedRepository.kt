package hu.bme.mit.ftsrg.deprecated

interface KeyBasedRepository<EntityType, KeyType> {
  fun all(): List<EntityType>
  fun byID(id: KeyType): EntityType?
  fun add(entity: EntityType)
  fun remove(id: KeyType)
}