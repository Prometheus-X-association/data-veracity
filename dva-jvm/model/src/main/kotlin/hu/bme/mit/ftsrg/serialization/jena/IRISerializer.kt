package hu.bme.mit.ftsrg.serialization.jena

import kotlinx.serialization.KSerializer
import kotlinx.serialization.descriptors.PrimitiveKind
import kotlinx.serialization.descriptors.PrimitiveSerialDescriptor
import kotlinx.serialization.descriptors.SerialDescriptor
import kotlinx.serialization.encoding.Decoder
import kotlinx.serialization.encoding.Encoder
import org.apache.jena.iri.IRI
import org.apache.jena.iri.IRIFactory

object IRISerializer : KSerializer<IRI> {

  private val iriFactory = IRIFactory.iriImplementation()

  override val descriptor: SerialDescriptor = PrimitiveSerialDescriptor("IRI", PrimitiveKind.STRING)

  override fun deserialize(decoder: Decoder): IRI = iriFactory.create(decoder.decodeString())

  override fun serialize(encoder: Encoder, value: IRI) = encoder.encodeString(value.toString())
}