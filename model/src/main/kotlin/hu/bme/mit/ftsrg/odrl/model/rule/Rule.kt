package hu.bme.mit.ftsrg.odrl.model.rule

import hu.bme.mit.ftsrg.odrl.model.asset.Asset
import hu.bme.mit.ftsrg.odrl.model.party.Party
import org.apache.jena.iri.IRI

data class Rule(
  override val action: Action,
  override val relation: Asset? = null,
  override val function: List<Party>? = null,
  override val failure: List<Rule>? = null,
  override val uid: List<IRI>? = null,
) : IRule
