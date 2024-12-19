package hu.bme.mit.ftsrg.odrl.model.party

import hu.bme.mit.ftsrg.odrl.model.constraint.Constraint
import org.apache.jena.iri.IRI

data class PartyCollection(
  val source: IRI? = null,
  val refinement: List<Constraint>? = null,
  val party: Party
) : IParty by party
