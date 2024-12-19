package hu.bme.mit.ftsrg.odrl.model.rule

import hu.bme.mit.ftsrg.odrl.model.asset.Asset
import hu.bme.mit.ftsrg.odrl.model.party.Party
import org.apache.jena.iri.IRI

interface IRule {
  val action: Action
  val relation: Asset?
  val function: List<Party>?
  val failure: List<Rule>?
  val uid: List<IRI>?
}