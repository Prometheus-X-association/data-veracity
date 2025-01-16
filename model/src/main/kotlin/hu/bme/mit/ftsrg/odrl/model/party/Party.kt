@file:UseSerializers(IRISerializer::class)

package hu.bme.mit.ftsrg.odrl.model.party

import hu.bme.mit.ftsrg.serialization.IRISerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import org.apache.jena.iri.IRI

@Serializable
data class Party(override val uid: IRI? = null, override val partOf: List<PartyCollection>? = null) : IParty
