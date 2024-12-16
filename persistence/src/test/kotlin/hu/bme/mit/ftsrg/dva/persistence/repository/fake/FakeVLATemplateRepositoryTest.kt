package hu.bme.mit.ftsrg.dva.persistence.repository.fake

import hu.bme.mit.ftsrg.dva.model.vla.*
import hu.bme.mit.ftsrg.dva.persistence.error.EntityExistsException
import hu.bme.mit.ftsrg.dva.persistence.error.EntityNotFoundException
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.assertThrows

class FakeVLATemplateRepositoryTest {

  private lateinit var repository: FakeVLATemplateRepository

  private val testTemplate = VLATemplate(
    id = "template-0000",
    objective = VeracityObjective(
      evaluationScheme = EvaluationScheme(
        evaluationMethod = "syntax check",
        criterionType = CriterionType.VALID_INVALID
      ),
      targetAspect = QualityAspect.SYNTAX
    )
  )

  @BeforeEach
  fun setup() {
    repository = FakeVLATemplateRepository()
  }

  @Test
  fun `should contain default entities after initialization`() {
    assertEquals(2, repository.allTemplates().size)
  }

  @Test
  fun `should be able to create new templates`() {
    repository.addTemplate(testTemplate)
    val retrieved: VLATemplate? = repository.templateById(testTemplate.id)
    assertEquals(testTemplate, retrieved)
  }

  @Test
  fun `should throw entity exists exception when creating entity with existing ID`() {
    assertThrows<EntityExistsException> { repository.addTemplate(repository.templateById("template-0001")!!) }
  }

  @Test
  fun `should return null when nonexistent entity requested`() {
    assertNull(repository.templateById("non-existing"))
  }

  @Test
  fun `should throw entity not found exception when asking to delete entity with nonexisent ID`() {
    assertThrows<EntityNotFoundException> { repository.removeTemplate("non-existing") }
  }

  @Test
  fun `should remove templates`() {
    repository.allTemplates().map { it.id }.forEach(repository::removeTemplate)
    assertEquals(0, repository.allTemplates().size)
  }
}