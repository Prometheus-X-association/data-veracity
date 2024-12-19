package hu.bme.mit.ftsrg.odrl.model.policy

import hu.bme.mit.ftsrg.odrl.model.rule.Rule
import org.apache.jena.iri.IRI

interface IPolicy {
  val uid: IRI
  val permission: List<Rule>
  val prohibition: List<Rule>
  val obligation: List<Rule>
  val profile: List<IRI>?
  val inheritFrom: List<IRI>?
  val conflict: ConflictTerm?
}