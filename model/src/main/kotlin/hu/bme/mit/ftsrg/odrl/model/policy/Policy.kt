package hu.bme.mit.ftsrg.odrl.model.policy

import hu.bme.mit.ftsrg.odrl.model.rule.IRule
import hu.bme.mit.ftsrg.odrl.model.rule.Rule
import org.apache.jena.iri.IRI

data class Policy(
  override val uid: IRI,
  override val permission: List<IRule> = emptyList(),
  override val prohibition: List<IRule> = emptyList(),
  override val obligation: List<IRule> = emptyList(),
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