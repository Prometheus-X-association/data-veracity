package hu.bme.mit.ftsrg.odrl.model.asset

import hu.bme.mit.ftsrg.serialization.AssetSerializer
import kotlinx.serialization.Serializable
import org.apache.jena.iri.IRI

@Serializable(with = AssetSerializer::class)
data class Asset(override val uid: IRI? = null, override val partOf: List<AssetCollection>? = null) : IAsset
