package hu.bme.mit.ftsrg.contractmanager.contract.model

import kotlinx.serialization.Serializable

/**
 * Dummy contract purpose class.
 */
@Serializable
data class Purpose(val purpose: String, val piiCategory: List<String>)
