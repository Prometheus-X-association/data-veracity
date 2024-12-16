package hu.bme.mit.ftsrg.dva.dto.vla

import hu.bme.mit.ftsrg.dva.model.vla.CriterionType
import hu.bme.mit.ftsrg.dva.model.vla.EvaluationScheme
import hu.bme.mit.ftsrg.dva.model.vla.QualityAspect
import hu.bme.mit.ftsrg.dva.model.vla.VeracityObjective
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class VeracityObjectiveDTOTest {

  private val bo: VeracityObjective = VeracityObjective(
    evaluationScheme = EvaluationScheme(
      evaluationMethod = "syntax check",
      criterionType = CriterionType.VALID_INVALID
    ),
    targetAspect = QualityAspect.SYNTAX
  )

  private val dto: VeracityObjectiveDTO = VeracityObjectiveDTO(
    evaluationScheme = EvaluationSchemeDTO(
      evaluationMethod = "syntax check",
      criterionType = CriterionTypeDTO.VALID_INVALID
    ),
    targetAspect = QualityAspectDTO.SYNTAX
  )

  @Test
  fun `should correctly map to business object`() {
    assertEquals(bo, dto.toBO())
  }

  @Test
  fun `should correctly map from business object`() {
    assertEquals(dto, VeracityObjectiveDTO.fromBO(bo))
  }
}