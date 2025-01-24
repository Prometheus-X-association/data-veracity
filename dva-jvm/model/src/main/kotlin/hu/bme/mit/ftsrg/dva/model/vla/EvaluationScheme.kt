package hu.bme.mit.ftsrg.dva.model.vla

import kotlinx.serialization.Serializable

@Serializable
data class EvaluationScheme(val evaluationMethod: String, val criterionType: CriterionType)
