package hu.bme.mit.ftsrg.dva.vla

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject

@Serializable
data class Template(
    val id: String,
    val name: String,
    val description: String? = null,
    val criterionType: CriterionType,
    val targetAspect: QualityAspect,
    val evaluationMethod: EvaluationMethod
)

@Serializable
data class EvaluationMethod(val engine: Engine, val variableSchema: JsonObject, val implementationTemplate: String)

@Serializable
enum class Engine { SCHEMA, GREAT_EXPECTATIONS, JQ }

@Serializable
enum class CriterionType { VALID_INVALID, IN_RANGE, GREATER_THAN, LESS_THAN }

@Serializable
enum class QualityAspect { SYNTAX, TIMELINESS, ACCURACY, COMPLETENESS, CONSISTENCY }

@Serializable
data class NewTemplate(
    val name: String,
    val description: String? = null,
    val criterionType: CriterionType,
    val targetAspect: QualityAspect,
    val evaluationMethod: EvaluationMethod
)

@Serializable
data class TemplatePatch(
    val id: String,
    val name: String? = null,
    val description: String? = null,
    val criterionType: CriterionType? = null,
    val targetAspect: QualityAspect? = null,
    val evaluationMethod: EvaluationMethod? = null
)