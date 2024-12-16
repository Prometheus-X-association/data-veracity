package hu.bme.mit.ftsrg.dva.dto.vla

import kotlinx.serialization.Serializable
import hu.bme.mit.ftsrg.dva.model.vla.VLATemplate as VLABO

@Serializable
data class VLATemplateDTO(val id: String, val objective: VeracityObjectiveDTO) {
  companion object {
    fun fromBO(bo: VLABO): VLATemplateDTO = VLATemplateDTO(bo.id, VeracityObjectiveDTO.fromBO(bo.objective))
  }

  fun toBO(): VLABO = VLABO(id, objective.toBO())
}
