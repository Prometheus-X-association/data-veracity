package hu.bme.mit.ftsrg.dva.api.dto

import hu.bme.mit.ftsrg.contractmanager.contract.model.Contract
import java.net.URL

data class AttestationRequest(val contract: Contract, val data: ByteArray, val attesterID: String, val callbackURL: URL)
