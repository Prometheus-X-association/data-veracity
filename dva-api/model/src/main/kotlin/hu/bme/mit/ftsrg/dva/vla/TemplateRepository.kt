package hu.bme.mit.ftsrg.dva.vla

interface TemplateRepository {
    fun allTemplates(): List<Template>
    fun templateById(id: String): Template?
    fun addTemplate(template: NewTemplate): Template?
    fun patchTemplate(patch: TemplatePatch): Template?
    fun removeTemplate(id: String): Boolean
}