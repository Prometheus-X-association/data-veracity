package hu.bme.mit.ftsrg.odrl.model.constraint

import hu.bme.mit.ftsrg.odrl.model.policy.ConflictTerm
import hu.bme.mit.ftsrg.odrl.model.toW3CInstanceName
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class W3CConformanceTest {

  @Test
  fun `should return correct W3C camel cased name for LeftOperand`() {
    assertEquals("absoluteTemporalPosition", LeftOperand.ABSOLUTE_TEMPORAL_POSITION.toW3CInstanceName())
  }

  @Test
  fun `should return correct W3C camel cased name for Operator`() {
    assertEquals("isAllOf", Operator.IS_ALL_OF.toW3CInstanceName())
  }

  @Test
  fun `should return correct W3C camel cased name for RightOperand`() {
    assertEquals("policyUsage", RightOperand.POLICY_USAGE.toW3CInstanceName())
  }

  @Test
  fun `should return correct W3C camel cased name for ConflictTerm`() {
    assertEquals("invalid", ConflictTerm.INVALID.toW3CInstanceName())
  }
}