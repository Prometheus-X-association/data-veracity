package hu.bme.mit.ftsrg.dva.dto.vla

import hu.bme.mit.ftsrg.dva.model.vla.QualityAspect
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class QualityAspectDTOTest {

  private val bo: QualityAspect = QualityAspect.SYNTAX
  private val dto: QualityAspectDTO = QualityAspectDTO.SYNTAX

  @Test
  fun `should correctly map to business object`() {
    assertEquals(bo, dto.toBO())
  }

  @Test
  fun `should correctly map from business object`() {
    assertEquals(dto, QualityAspectDTO.fromBO(bo))
  }
}