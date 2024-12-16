package hu.bme.mit.ftsrg.dva.dto.vla

import kotlinx.serialization.Serializable
import hu.bme.mit.ftsrg.dva.model.vla.EvaluationScheme as ESBO

@Serializable
data class EvaluationSchemeDTO(val evaluationMethod: String, val criterionType: CriterionTypeDTO) {
  companion object {
    fun fromBO(bo: ESBO): EvaluationSchemeDTO =
      EvaluationSchemeDTO(bo.evaluationMethod, CriterionTypeDTO.fromBO(bo.criterionType))
  }

  fun toBO(): ESBO = ESBO(evaluationMethod, criterionType.toBO())
}
