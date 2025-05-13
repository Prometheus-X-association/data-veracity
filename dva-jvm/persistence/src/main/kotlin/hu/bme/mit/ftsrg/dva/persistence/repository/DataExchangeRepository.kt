package hu.bme.mit.ftsrg.dva.persistence.repository

import hu.bme.mit.ftsrg.connector.model.DataExchange

interface DataExchangeRepository : KeyBasedRepository<DataExchange, String>