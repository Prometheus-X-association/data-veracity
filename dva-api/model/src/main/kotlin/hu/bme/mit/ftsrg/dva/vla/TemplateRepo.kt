package hu.bme.mit.ftsrg.dva.vla

import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class)
interface TemplateRepo {
    suspend fun allTemplates(): List<Template>
    suspend fun templateById(id: Uuid): Template?
    suspend fun addTemplate(template: TemplateNew): Template?
    suspend fun patchTemplate(patch: TemplatePatch): Template?
    suspend fun removeTemplate(id: Uuid): Boolean
}