@file:UseSerializers(IRISerializer::class)

package hu.bme.mit.ftsrg.odrl.model.party

import hu.bme.mit.ftsrg.odrl.model.constraint.Constraint
import hu.bme.mit.ftsrg.serialization.jena.IRISerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import org.apache.jena.iri.IRI

@Serializable
data class PartyCollection(
  val source: IRI? = null,
  val refinement: List<Constraint>? = null,
  val party: Party
) : IParty by party
