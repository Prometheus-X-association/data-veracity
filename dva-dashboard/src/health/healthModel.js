// Turns the gateway's `/info/health` answer – every service's `/readyz`,
// `{ gateway: { status, output }, processing: {...}, ... }`, see
// docs/health-checks.md – into one dashboard row per service.

export const HEALTH_ENDPOINT = '/api/info/health'

const SERVICES = [
  { key: 'gateway', name: 'DVA API gateway', description: 'Routing and attestation flow', icon: 'fa-route' },
  { key: 'vla-manager', name: 'VLA Manager', description: 'Veracity level agreements', icon: 'fa-file-contract' },
  { key: 'processing', name: 'Evaluation processing', description: 'Schema, JQ and quality engines', icon: 'fa-microchip' },
  { key: 'vc-manager', name: 'Credential service', description: 'Verifiable credential issuance', icon: 'fa-certificate' }
]

const ROW_STATUS = { pass: 'operational', warn: 'degraded', fail: 'unavailable' }

const LABELS = { operational: 'Operational', degraded: 'Degraded', unavailable: 'Unavailable', checking: 'Checking' }

export function statusLabel (status) {
  return LABELS[status] || 'Unknown'
}

const rows = (row) => SERVICES.map(service => ({ ...service, latency: '', detail: null, ...row(service) }))

export const checkingRows = () => rows(() => ({ status: 'checking', latency: 'Checking' }))
export const demoRows = () => rows(() => ({ status: 'operational', latency: 'Demo' }))
export const unreachableRows = () => rows(() => ({ status: 'unavailable', latency: 'Unavailable', detail: 'The gateway did not answer.' }))

// `latencyMs` is how long the gateway took to answer, shown on its own row.
export function rowsFromHealth (report, latencyMs) {
  return rows(service => {
    const health = report?.[service.key]
    return {
      status: ROW_STATUS[health?.status] ?? 'unavailable',
      detail: health ? health.output ?? null : 'Not reported by the gateway.',
      latency: service.key === 'gateway' ? `${Math.max(1, Math.round(latencyMs))} ms` : ''
    }
  })
}

// 'healthy' | 'warning' | 'degraded' | 'checking', matching the badge styles.
export function overallTone (rows) {
  if (rows.some(row => row.status === 'unavailable')) return 'degraded'
  if (rows.some(row => row.status === 'checking')) return 'checking'
  if (rows.some(row => row.status === 'degraded')) return 'warning'
  return 'healthy'
}

export function overallLabel (tone) {
  return { healthy: 'All checks passed', warning: 'Partially degraded', degraded: 'Action required', checking: 'Checking services' }[tone]
}

export function overallNote (tone) {
  return {
    healthy: 'Every service is ready.',
    warning: 'Every service works, but some report degraded functionality.',
    degraded: 'At least one service is not ready; attestation requests may fail until it recovers.',
    checking: 'The dashboard is asking the gateway for the health of every service.'
  }[tone]
}
