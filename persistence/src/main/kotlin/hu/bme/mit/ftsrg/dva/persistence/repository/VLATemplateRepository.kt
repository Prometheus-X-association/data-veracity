package hu.bme.mit.ftsrg.dva.persistence.repository

import hu.bme.mit.ftsrg.dva.model.vla.VLATemplate

interface VLATemplateRepository {
  fun allTemplates(): List<VLATemplate>
  fun templateById(id: String): VLATemplate?
  fun addTemplate(template: VLATemplate)
  fun removeTemplate(id: String)
}