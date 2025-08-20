package hu.bme.mit.ftsrg.dva.vla

import hu.bme.mit.ftsrg.dva.vla.CriterionType.VALID_INVALID
import hu.bme.mit.ftsrg.dva.vla.QualityAspect.SYNTAX
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonObject
import java.util.*

class FakeTemplateRepository : TemplateRepository {
    private val templates = mutableMapOf(
        "template-0000" to Template(
            id = "template-0000",
            name = "JSON Schema",
            description = "Data should conform to a JSON schema with the given URL",
            criterionType = VALID_INVALID,
            targetAspect = SYNTAX,
            evaluationMethod = EvaluationMethod(
                engine = Engine.SCHEMA,
                variableSchema = buildJsonObject {
                    put("type", "object")
                    putJsonObject("properties") {
                        putJsonObject("schemaURL") {
                            put("type", "string")
                            put("format", "uri")
                        }
                    }
                },
                implementationTemplate = "\${schemaURL}"
            )
        )
    )

    override fun allTemplates(): List<Template> {
        return templates.values.toList()
    }

    override fun templateById(id: String): Template? {
        return templates[id]
    }

    override fun addTemplate(template: NewTemplate): Template? {
        val entity = Template(
            id = UUID.randomUUID().toString(),
            name = template.name,
            description = template.description,
            criterionType = template.criterionType,
            targetAspect = template.targetAspect,
            evaluationMethod = template.evaluationMethod
        )
        templates.put(entity.id, entity)
        return entity
    }

    override fun patchTemplate(patch: TemplatePatch): Template? {
        val existingTemplate = templates[patch.id] ?: return null

        val patchedTemplate = Template(
            id = patch.id,
            name = patch.name ?: existingTemplate.name,
            description = patch.description ?: existingTemplate.description,
            criterionType = patch.criterionType ?: existingTemplate.criterionType,
            targetAspect = patch.targetAspect ?: existingTemplate.targetAspect,
            evaluationMethod = patch.evaluationMethod ?: existingTemplate.evaluationMethod
        )

        templates.put(patch.id, patchedTemplate)
        return patchedTemplate
    }

    override fun removeTemplate(id: String): Boolean {
        if (templates[id] == null) return false
        templates.remove(id)
        return true
    }
}