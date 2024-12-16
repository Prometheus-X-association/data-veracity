package hu.bme.mit.ftsrg.dva.dto.vla

import hu.bme.mit.ftsrg.dva.model.vla.CriterionType
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class CriterionTypeDTOTest {

  private val bo: CriterionType = CriterionType.VALID_INVALID
  private val dto: CriterionTypeDTO = CriterionTypeDTO.VALID_INVALID

  @Test
  fun `should correctly map to business object`() {
    assertEquals(bo, dto.toBO())
  }

  @Test
  fun `should correctly map from business object`() {
    assertEquals(dto, CriterionTypeDTO.fromBO(bo))
  }
}