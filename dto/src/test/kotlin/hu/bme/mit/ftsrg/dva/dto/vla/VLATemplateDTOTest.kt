package hu.bme.mit.ftsrg.dva.dto.vla

import hu.bme.mit.ftsrg.dva.model.vla.*
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class VLATemplateDTOTest {

  private val bo: VLATemplate = VLATemplate(
    id = "template-0000",
    objective = VeracityObjective(
      evaluationScheme = EvaluationScheme(
        evaluationMethod = "syntax check",
        criterionType = CriterionType.VALID_INVALID
      ),
      targetAspect = QualityAspect.SYNTAX
    )
  )

  private val dto: VLATemplateDTO = VLATemplateDTO(
    id = "template-0000",
    objective = VeracityObjectiveDTO(
      evaluationScheme = EvaluationSchemeDTO(
        evaluationMethod = "syntax check",
        criterionType = CriterionTypeDTO.VALID_INVALID
      ),
      targetAspect = QualityAspectDTO.SYNTAX
    )
  )

  @Test
  fun `should correctly map to business object`() {
    assertEquals(bo, dto.toBO())
  }

  @Test
  fun `should correctly map from business object`() {
    assertEquals(dto, VLATemplateDTO.fromBO(bo))
  }
}