package hu.bme.mit.ftsrg.odrl.model.asset

import org.apache.jena.iri.IRI

interface IAsset {
  val uid: IRI?
  val partOf: List<AssetCollection>?
}