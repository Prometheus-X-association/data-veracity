package hu.bme.mit.ftsrg.odrl.model.rule

import hu.bme.mit.ftsrg.odrl.model.asset.Asset
import hu.bme.mit.ftsrg.odrl.model.party.Party

data class Prohibition(
  val target: Asset,
  val assigner: Party? = null,
  val assignee: Party? = null,
  val remedy: List<Duty>? = null,
  val rule: Rule,
) : IRule by rule
