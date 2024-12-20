package hu.bme.mit.ftsrg.odrl.model.rule

import hu.bme.mit.ftsrg.odrl.model.asset.Asset
import hu.bme.mit.ftsrg.odrl.model.party.Party
import kotlinx.serialization.Serializable

@Serializable
data class Duty(
  val target: Asset? = null,
  val assigner: Party? = null,
  val assignee: Party? = null,
  val consequence: List<Duty>? = null,
  val rule: Rule,
) : IRule by rule
