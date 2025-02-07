package hu.bme.mit.ftsrg.dva.model.aov

import hu.bme.mit.ftsrg.vc.model.IVerifiableCredential
import hu.bme.mit.ftsrg.vc.model.VerifiableCredential
import kotlinx.serialization.Contextual
import kotlinx.serialization.Serializable

@Serializable
data class AttestationOfVeracity(
  val aovID: String,
  val contractId: String,
  val evaluations: List<Evaluation>,
  @Contextual val vc: VerifiableCredential
) : IVerifiableCredential by vc