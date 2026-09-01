import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { globSync } from 'node:fs'

import { dashboardEndpoints } from '../dva-dashboard/src/api/endpoints.js'

test('routes dashboard data to the services that own it', () => {
  assert.deepEqual(dashboardEndpoints, {
    requests: '/api/dva/info/requests',
    vlas: '/api/vla/vla',
    credentials: '/api/vc/admin/credentials',
    verifications: '/api/vc/admin/verifications'
  })
})

test('does not retain removed ACA-Py and message-queue behavior', () => {
  const files = globSync([
    'dva-dashboard/src/**/*.{js,vue}',
    'vla-manager/src/**/*.{js,vue}'
  ])
  const source = files.map(file => readFileSync(file, 'utf8')).join('\n')
  const dashboardSource = globSync('dva-dashboard/src/**/*.{js,vue}')
    .map(file => readFileSync(file, 'utf8')).join('\n')
  const forbidden = [
    /ACA-Py/i,
    /present-proof/i,
    /credential exchange/i,
    /presentation exchange/i,
    /queued attestation/i,
    /QUEUE_FAILURE/,
    /RabbitMQ/i,
    /\/api\/info\/credentials/,
    /\/api\/info\/presentations/
  ]

  for (const pattern of forbidden) {
    assert.doesNotMatch(source, pattern)
  }
  assert.doesNotMatch(dashboardSource, /axios\.get\(['"]\/api\/info\/requests/)
  assert.doesNotMatch(dashboardSource, /axios\.get\(['"]\/api\/vla['"]/) 
})

test('routes production requests to the three HTTP services', () => {
  const nginx = readFileSync('dva-dashboard/misc/nginx.conf.template', 'utf8')
  assert.match(nginx, /location \/api\/dva\//)
  assert.match(nginx, /location \/api\/vla\//)
  assert.match(nginx, /location \/api\/vc\//)
  assert.match(nginx, /VLA_MANAGER_API_URL/)
  assert.match(nginx, /VC_MANAGER_API_URL/)
})
