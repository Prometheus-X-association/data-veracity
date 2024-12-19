package hu.bme.mit.ftsrg.odrl.model.asset

import org.apache.jena.iri.IRI

data class Asset(override val uid: IRI? = null, override val partOf: List<AssetCollection>? = null) : IAsset
