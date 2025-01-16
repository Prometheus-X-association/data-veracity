package hu.bme.mit.ftsrg.odrl.model

import dev.turingcomplete.textcaseconverter.StandardTextCases.STRICT_CAMEL_CASE
import dev.turingcomplete.textcaseconverter.StandardWordsSplitters.UNDERSCORE
import dev.turingcomplete.textcaseconverter.toTextCase
import hu.bme.mit.ftsrg.odrl.model.constraint.LeftOperand
import hu.bme.mit.ftsrg.odrl.model.constraint.Operator
import hu.bme.mit.ftsrg.odrl.model.constraint.RightOperand
import hu.bme.mit.ftsrg.odrl.model.policy.ConflictTerm
import hu.bme.mit.ftsrg.odrl.model.rule.Action

private fun String.toW3CInstanceName() = toTextCase(textCase = STRICT_CAMEL_CASE, originWordsSplitter = UNDERSCORE)

fun LeftOperand.toW3CInstanceName() = name.toW3CInstanceName()
fun Operator.toW3CInstanceName() = name.toW3CInstanceName()
fun RightOperand.toW3CInstanceName() = name.toW3CInstanceName()
fun Action.toW3CInstanceName() = w3cInstance
fun ConflictTerm.toW3CInstanceName() = name.toW3CInstanceName()
