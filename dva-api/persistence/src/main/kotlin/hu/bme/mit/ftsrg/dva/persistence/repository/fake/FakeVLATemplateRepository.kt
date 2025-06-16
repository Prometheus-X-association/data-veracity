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

  override fun all(): List<VLATemplate> = templates.values.toList()

  override fun byID(id: String): VLATemplate? = templates[id]

  override fun add(entity: VLATemplate) {
    if (byID(entity.id) != null) throw EntityExistsException("Template with id ${entity.id} already exists")
    templates[entity.id] = entity
  }

  override fun remove(id: String) {
    if (byID(id) == null) throw EntityNotFoundException("Template with id $id does not exist")
    templates.remove(id)
  }
}