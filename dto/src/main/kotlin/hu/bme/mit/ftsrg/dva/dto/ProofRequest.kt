package hu.bme.mit.ftsrg.dva.dto

import hu.bme.mit.ftsrg.contractmanager.contract.model.Contract
import java.net.URL

data class ProofRequest(val contract: Contract, val data: ByteArray, val proverID: String, val callbackURL: URL)
