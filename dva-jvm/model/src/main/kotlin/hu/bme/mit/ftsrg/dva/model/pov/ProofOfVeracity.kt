package hu.bme.mit.ftsrg.dva.model.pov

import hu.bme.mit.ftsrg.vc.model.IVerifiableCredential
import hu.bme.mit.ftsrg.vc.model.VerifiableCredential
import kotlinx.serialization.Contextual
import kotlinx.serialization.Serializable

@Serializable
data class ProofOfVeracity(
  val povID: String,
  val contractId: String,
  val proof: ByteArray,
  @Contextual val vc: VerifiableCredential
) : IVerifiableCredential by vc