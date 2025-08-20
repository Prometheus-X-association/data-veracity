package hu.bme.mit.ftsrg.dva.vla

import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class)
interface TemplateRepository {
    suspend fun allTemplates(): List<Template>
    suspend fun templateById(id: Uuid): Template?
    suspend fun addTemplate(template: NewTemplate): Template?
    suspend fun patchTemplate(patch: TemplatePatch): Template?
    suspend fun removeTemplate(id: Uuid): Boolean
}