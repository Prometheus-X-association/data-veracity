package hu.bme.mit.ftsrg.dva.dto.vla

import kotlinx.serialization.Serializable

import hu.bme.mit.ftsrg.dva.model.vla.VeracityObjective as VOBO

@Serializable
data class VeracityObjectiveDTO(val evaluationScheme: EvaluationSchemeDTO, val targetAspect: QualityAspectDTO) {
  companion object {
    fun fromBO(bo: VOBO): VeracityObjectiveDTO =
      VeracityObjectiveDTO(EvaluationSchemeDTO.fromBO(bo.evaluationScheme), QualityAspectDTO.fromBO(bo.targetAspect))
  }

  fun toBO(): VOBO = VOBO(evaluationScheme.toBO(), targetAspect.toBO())
}