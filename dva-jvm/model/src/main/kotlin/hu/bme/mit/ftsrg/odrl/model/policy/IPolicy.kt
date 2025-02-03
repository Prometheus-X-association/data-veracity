package hu.bme.mit.ftsrg.odrl.model.policy

import hu.bme.mit.ftsrg.odrl.model.rule.IRule
import org.apache.jena.iri.IRI

interface IPolicy {
  val uid: IRI
  val permission: List<IRule>
  val prohibition: List<IRule>
  val obligation: List<IRule>
  val profile: List<IRI>?
  val inheritFrom: List<IRI>?
  val conflict: ConflictTerm?
}