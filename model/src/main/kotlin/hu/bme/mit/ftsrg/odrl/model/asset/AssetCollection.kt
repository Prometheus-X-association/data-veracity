package hu.bme.mit.ftsrg.odrl.model.asset

import hu.bme.mit.ftsrg.odrl.model.constraint.Constraint
import org.apache.jena.iri.IRI

data class AssetCollection(
  val source: IRI? = null,
  val refinement: List<Constraint>? = null,
  val asset: Asset
) : IAsset by asset
