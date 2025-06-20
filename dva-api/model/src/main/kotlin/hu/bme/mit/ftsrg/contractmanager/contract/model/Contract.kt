package hu.bme.mit.ftsrg.contractmanager.contract.model

import hu.bme.mit.ftsrg.odrl.model.policy.Policy
import kotlinx.serialization.Serializable
import hu.bme.mit.ftsrg.odcs.model.Contract as ODCSContract

/**
 * Dummy contract schema.
 */
@Serializable
data class Contract(
  val id: String,
  val dataProvider: String,
  val dataConsumer: String,
  val serviceOffering: String,
  val purpose: List<Purpose>,
  val negotiators: List<Negotiator>,
  val status: Status,
  val policy: List<Policy>,
  val vla: ODCSContract,
)
