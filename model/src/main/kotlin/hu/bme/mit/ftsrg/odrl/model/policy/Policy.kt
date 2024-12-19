package hu.bme.mit.ftsrg.odrl.model.policy

import hu.bme.mit.ftsrg.odrl.model.rule.Rule
import org.apache.jena.iri.IRI

data class Policy(
  override val uid: IRI,
  override val permission: List<Rule>,
  override val prohibition: List<Rule>,
  override val obligation: List<Rule>,
  override val profile: List<IRI>? = null,
  override val inheritFrom: List<IRI>? = null,
  override val conflict: ConflictTerm? = null,
) : IPolicy {

  init {
    require(permission.size + prohibition.size + obligation.size > 0) {
      "There must be at least one permission/prohibition/obligation in the policy"
    }
  }
}