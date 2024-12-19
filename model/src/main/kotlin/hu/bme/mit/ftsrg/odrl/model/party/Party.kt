package hu.bme.mit.ftsrg.odrl.model.party

import org.apache.jena.iri.IRI

data class Party(override val uid: IRI? = null, override val partOf: List<PartyCollection>? = null) : IParty
