package hu.bme.mit.ftsrg.odrl.model.constraint

import org.apache.jena.iri.IRI

/**
 * A partially compliant ODRL 2.2 Constraint class.
 */
data class Constraint(
  val uid: IRI? = null,
  val leftOperand: LeftOperand,
  val operator: Operator,
  val rightOperandLiteral: String? = null,
  val rightOperandIRI: IRI? = null,
  val rightOperand: RightOperand? = null,
  val rightOperandReference: IRI? = null,
  val rightOperandReferences: List<IRI>? = null,
  val dataType: String? = null,
  val unit: String? = null,
  val status: String? = null,
) {

  init {
    require(
      listOf(
        rightOperandLiteral,
        rightOperandIRI,
        rightOperand,
        rightOperandReference,
        rightOperandReferences
      ).count { it != null } == 1) {
      "Exactly one of {rightOperandLiteral, rightOperandIRI, rightOperand, rightOperandReference, rightOperandReferences} must be specified"
    }
  }
}