package hu.bme.mit.ftsrg.dva.dto.vla

import hu.bme.mit.ftsrg.dva.model.vla.CriterionType
import hu.bme.mit.ftsrg.dva.model.vla.EvaluationScheme
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class EvaluationSchemeDTOTest {

  private val bo: EvaluationScheme = EvaluationScheme(
    evaluationMethod = "syntax check",
    criterionType = CriterionType.VALID_INVALID
  )

  private val dto: EvaluationSchemeDTO = EvaluationSchemeDTO(
    evaluationMethod = "syntax check",
    criterionType = CriterionTypeDTO.VALID_INVALID
  )

  @Test
  fun `should correctly map to business object`() {
    assertEquals(bo, dto.toBO())
  }

  @Test
  fun `should correctly map from business object`() {
    assertEquals(dto, EvaluationSchemeDTO.fromBO(bo))
  }
}