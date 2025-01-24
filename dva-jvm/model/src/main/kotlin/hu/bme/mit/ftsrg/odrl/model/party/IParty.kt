package hu.bme.mit.ftsrg.odrl.model.party

import org.apache.jena.iri.IRI

interface IParty {
  val uid: IRI?
  val partOf: List<PartyCollection>?
}