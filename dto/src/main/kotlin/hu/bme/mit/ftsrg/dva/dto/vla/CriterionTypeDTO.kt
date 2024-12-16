package hu.bme.mit.ftsrg.dva.dto.vla

import hu.bme.mit.ftsrg.dva.model.vla.CriterionType as CTBO

enum class CriterionTypeDTO {
  VALID_INVALID, WITHIN_RANGE, GREATER_OR_LESS_THAN;

  companion object {
    fun fromBO(bo: CTBO): CriterionTypeDTO = when (bo) {
      CTBO.VALID_INVALID -> VALID_INVALID
      CTBO.WITHIN_RANGE -> WITHIN_RANGE
      CTBO.GREATER_OR_LESS_THAN -> GREATER_OR_LESS_THAN
    }
  }

  fun toBO(): CTBO = when (this) {
    VALID_INVALID -> CTBO.VALID_INVALID
    WITHIN_RANGE -> CTBO.WITHIN_RANGE
    GREATER_OR_LESS_THAN -> CTBO.GREATER_OR_LESS_THAN
  }
}
