package hu.bme.mit.ftsrg.dva.model.vla

import kotlinx.serialization.Serializable

@Serializable
data class VeracityObjective(val evaluationScheme: EvaluationScheme, val targetAspect: QualityAspect)
