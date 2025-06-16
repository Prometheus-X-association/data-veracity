package hu.bme.mit.ftsrg.serialization.odrl

import hu.bme.mit.ftsrg.odrl.model.asset.Asset
import kotlinx.serialization.KSerializer
import kotlinx.serialization.descriptors.PrimitiveKind
import kotlinx.serialization.descriptors.PrimitiveSerialDescriptor
import kotlinx.serialization.descriptors.SerialDescriptor
import kotlinx.serialization.encoding.Decoder
import kotlinx.serialization.encoding.Encoder
import org.apache.jena.iri.IRIFactory

object AssetSerializer : KSerializer<Asset> {

  private val iriFactory = IRIFactory.iriImplementation()

  override val descriptor: SerialDescriptor = PrimitiveSerialDescriptor("Asset", PrimitiveKind.STRING)

  override fun deserialize(decoder: Decoder): Asset = Asset(iriFactory.create(decoder.decodeString()))

  override fun serialize(encoder: Encoder, value: Asset) = encoder.encodeString(value.uid.toString())
}