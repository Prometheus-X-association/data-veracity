package hu.bme.mit.ftsrg.dva.persistence.repository.fake

import hu.bme.mit.ftsrg.connector.model.DataExchange
import hu.bme.mit.ftsrg.dva.persistence.repository.DataExchangeRepository

class FakeDataExchangeRepository : DataExchangeRepository {

  private val exchanges = mutableMapOf<String, DataExchange>()

  override fun all(): List<DataExchange> {
    return exchanges.values.toList()
  }

  override fun byID(id: String): DataExchange? {
    return exchanges[id]
  }

  override fun add(entity: DataExchange) {
    exchanges[entity.contract] = entity
  }

  override fun remove(id: String) {
    exchanges.remove(id)
  }
}