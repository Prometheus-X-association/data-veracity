<template>
  <n-modal
    :show="show"
    preset="card"
    :title="vla ? (vla.name || vlaPurpose(vla) || 'Unnamed VLA') : 'VLA details'"
    :style="{ width: 'min(860px, calc(100vw - 24px))' }"
    @update:show="value => emit('update:show', value)"
  >
    <div v-if="vla" class="details">
      <n-alert type="info" :show-icon="false" class="read-only-note">
        Read-only view of a saved VLA. To change a VLA, create a new one.
      </n-alert>

      <section>
        <h4>Contract</h4>
        <dl class="facts">
          <div><dt>ID</dt><dd class="mono">{{ vla.id }}</dd></div>
          <div v-if="vla.status"><dt>Status</dt><dd><n-tag size="small" type="success" round>{{ vla.status }}</n-tag></dd></div>
          <div v-if="vla.version"><dt>Version</dt><dd>{{ vla.version }}</dd></div>
          <div v-if="vla.kind"><dt>Kind</dt><dd>{{ vla.kind }}</dd></div>
          <div v-if="vla.apiVersion"><dt>ODCS version</dt><dd>{{ vla.apiVersion }}</dd></div>
          <div v-if="vla.dataReference"><dt>Data</dt><dd>{{ vla.dataReference }}</dd></div>
          <div class="wide"><dt>Purpose</dt><dd>{{ vlaPurpose(vla) || 'No description provided' }}</dd></div>
          <div v-if="vla.participants?.length" class="wide">
            <dt>Participants</dt>
            <dd><n-space size="small" :wrap="true"><n-tag v-for="p in vla.participants" :key="p" size="small" type="warning">{{ p }}</n-tag></n-space></dd>
          </div>
          <div v-if="vla.tags?.length" class="wide">
            <dt>Tags</dt>
            <dd><n-space size="small" :wrap="true"><n-tag v-for="tag in vla.tags" :key="tag" size="small" round>{{ tag }}</n-tag></n-space></dd>
          </div>
        </dl>
      </section>

      <section v-for="(schemaObject, index) in schemaObjects" :key="index">
        <h4>
          Data: <span class="mono">{{ schemaObject.name }}</span>
          <n-text v-if="schemaObject.logicalType" depth="3"> ({{ schemaObject.logicalType }})</n-text>
        </h4>

        <table v-if="schemaObject.properties.length" class="properties">
          <thead><tr><th>Property</th><th>Type</th><th>Required</th></tr></thead>
          <tbody>
            <tr v-for="property in schemaObject.properties" :key="property.name">
              <td class="mono">{{ property.name }}</td>
              <td>{{ property.logicalType || '—' }}</td>
              <td>{{ property.required ? 'Yes' : 'No' }}</td>
            </tr>
          </tbody>
        </table>

        <p v-if="!schemaObject.requirements.length" class="empty">This data object has no quality requirements.</p>
        <div v-for="(requirement, position) in schemaObject.requirements" :key="position" class="requirement">
          <div class="requirement-head">
            <strong>Requirement {{ position + 1 }}<template v-if="requirement.name">: {{ requirement.name }}</template></strong>
            <EngineBadge :engine="requirement.engine" />
          </div>
          <p v-if="requirement.description" class="requirement-description">{{ requirement.description }}</p>
          <dl class="facts compact">
            <div v-if="requirement.type"><dt>Type</dt><dd>{{ requirement.type }}</dd></div>
            <div v-if="requirement.dimension"><dt>Dimension</dt><dd>{{ requirement.dimension }}</dd></div>
          </dl>
          <pre v-if="requirementImplementation(requirement)" class="implementation">{{ requirementImplementation(requirement) }}</pre>
        </div>
      </section>

      <n-collapse>
        <n-collapse-item title="Raw VLA (JSON)" name="raw">
          <pre class="implementation">{{ JSON.stringify(vla, null, 2) }}</pre>
        </n-collapse-item>
      </n-collapse>
    </div>
  </n-modal>
</template>

<script setup>
import { computed } from 'vue'
import { NAlert, NCollapse, NCollapseItem, NModal, NSpace, NTag, NText } from 'naive-ui'
import EngineBadge from './EngineBadge.vue'
import { requirementImplementation, vlaPurpose, vlaSchemaObjects } from '../api/vla.js'

// A read-only view of one saved VLA: nothing here edits or sends it anywhere.
const props = defineProps({
  vla: { type: Object, default: null },
  show: { type: Boolean, default: false }
})
const emit = defineEmits(['update:show'])

const schemaObjects = computed(() => vlaSchemaObjects(props.vla))
</script>

<style scoped>
.details { display: grid; gap: 18px; }
.read-only-note { font-size: .78rem; }
h4 { margin: 0 0 8px; font-size: .85rem; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; overflow-wrap: anywhere; }
.facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px 16px; margin: 0; }
.facts > div { min-width: 0; }
.facts .wide { grid-column: 1 / -1; }
.facts dt { color: #64748b; font-size: .68rem; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; }
.facts dd { margin: 2px 0 0; font-size: .82rem; overflow-wrap: anywhere; }
.facts.compact { margin-top: 6px; }
.properties { width: 100%; border-collapse: collapse; margin-bottom: 12px; font-size: .78rem; }
.properties th { color: #64748b; font-size: .68rem; text-align: left; text-transform: uppercase; letter-spacing: .05em; }
.properties th, .properties td { padding: 6px 8px; border-bottom: 1px solid #e2e8f0; }
.empty { margin: 0; color: #64748b; font-size: .78rem; }
.requirement { display: grid; gap: 6px; margin-top: 10px; padding: 10px 12px; border: 1px solid #e2e8f0; border-radius: 6px; background: #f8fafc; }
.requirement-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap; font-size: .8rem; }
.requirement-description { margin: 0; font-size: .78rem; color: #475569; }
.implementation { margin: 0; max-height: 260px; overflow: auto; padding: 8px; border-radius: 4px; color: #334155; background: #fff; border: 1px solid #e2e8f0; font: .72rem/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; white-space: pre-wrap; overflow-wrap: anywhere; }
@media (max-width: 600px) { .facts { grid-template-columns: 1fr; } }
</style>
