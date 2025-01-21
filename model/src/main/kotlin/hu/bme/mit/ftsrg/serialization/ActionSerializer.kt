package hu.bme.mit.ftsrg.serialization

import hu.bme.mit.ftsrg.odrl.model.rule.Action
import kotlinx.serialization.KSerializer
import kotlinx.serialization.descriptors.PrimitiveKind
import kotlinx.serialization.descriptors.PrimitiveSerialDescriptor
import kotlinx.serialization.descriptors.SerialDescriptor
import kotlinx.serialization.encoding.Decoder
import kotlinx.serialization.encoding.Encoder

object ActionSerializer : KSerializer<Action> {

  override val descriptor: SerialDescriptor = PrimitiveSerialDescriptor("Action", PrimitiveKind.STRING)

  override fun deserialize(decoder: Decoder): Action = Action.valueOf(decoder.decodeString())

  override fun serialize(encoder: Encoder, value: Action) = encoder.encodeString(value.w3cInstance)
}