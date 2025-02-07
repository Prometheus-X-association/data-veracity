@file:UseSerializers(IRISerializer::class)

package hu.bme.mit.ftsrg.odrl.model.rule

import hu.bme.mit.ftsrg.odrl.model.asset.Asset
import hu.bme.mit.ftsrg.odrl.model.party.Party
import hu.bme.mit.ftsrg.serialization.jena.IRISerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import org.apache.jena.iri.IRI

@Serializable
data class Rule(
  override val action: Action,
  override val relation: Asset? = null,
  override val function: List<Party>? = null,
  override val failure: List<Rule>? = null,
  override val uid: List<IRI>? = null,
) : IRule
