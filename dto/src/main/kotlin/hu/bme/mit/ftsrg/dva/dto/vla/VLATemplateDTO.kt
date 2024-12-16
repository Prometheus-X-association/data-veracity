package hu.bme.mit.ftsrg.dva.dto.vla

import hu.bme.mit.ftsrg.dva.model.vla.VLATemplate as VLABO

data class VLATemplateDTO(val id: String, val objective: VeracityObjectiveDTO) {
  companion object {
    fun fromBO(bo: VLABO): VLATemplateDTO = VLATemplateDTO(bo.id, VeracityObjectiveDTO.fromBO(bo.objective))
  }

  fun toBO(): VLABO = VLABO(id, objective.toBO())
}
