package hu.bme.mit.ftsrg.dva.dto.vla

import hu.bme.mit.ftsrg.dva.model.vla.QualityAspect as QABO

enum class QualityAspectDTO {
  SYNTAX, TIMELINESS, ACCURACY, COMPLETENESS, CONSISTENCY;

  companion object {
    fun fromBO(bo: QABO): QualityAspectDTO = when (bo) {
      QABO.SYNTAX -> SYNTAX
      QABO.TIMELINESS -> TIMELINESS
      QABO.ACCURACY -> ACCURACY
      QABO.COMPLETENESS -> COMPLETENESS
      QABO.CONSISTENCY -> CONSISTENCY
    }
  }

  fun toBO(): QABO = when (this) {
    SYNTAX -> QABO.SYNTAX
    TIMELINESS -> QABO.TIMELINESS
    ACCURACY -> QABO.ACCURACY
    COMPLETENESS -> QABO.COMPLETENESS
    CONSISTENCY -> QABO.CONSISTENCY
  }
}
