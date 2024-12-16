package hu.bme.mit.ftsrg.dva.persistence.repository.fake

import hu.bme.mit.ftsrg.dva.model.vla.*
import hu.bme.mit.ftsrg.dva.persistence.error.EntityExistsException
import hu.bme.mit.ftsrg.dva.persistence.error.EntityNotFoundException
import hu.bme.mit.ftsrg.dva.persistence.repository.VLATemplateRepository

class FakeVLATemplateRepository : VLATemplateRepository {
  private val templates = mutableMapOf(
    "template-0001" to VLATemplate(
      "template-0001",
      VeracityObjective(
        evaluationScheme = EvaluationScheme(
          evaluationMethod = "syntax_check",
          criterionType = CriterionType.VALID_INVALID
        ),
        targetAspect = QualityAspect.SYNTAX
      )
    ),
    "template-0002" to VLATemplate(
      "template-0002",
      VeracityObjective(
        evaluationScheme = EvaluationScheme(
          evaluationMethod = "age_check",
          criterionType = CriterionType.WITHIN_RANGE
        ),
        targetAspect = QualityAspect.TIMELINESS
      )
    ),
  )

  override fun allTemplates(): List<VLATemplate> = templates.values.toList()

  override fun templateById(id: String): VLATemplate? = templates[id]

  override fun addTemplate(template: VLATemplate) {
    if (templateById(template.id) != null) throw EntityExistsException("Template with id ${template.id} already exists")
    templates[template.id] = template
  }

  override fun removeTemplate(id: String) {
    if (templateById(id) == null) throw EntityNotFoundException("Template with id $id does not exist")
    templates.remove(id)
  }
}