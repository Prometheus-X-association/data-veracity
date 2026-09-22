import test from 'node:test'
import assert from 'node:assert/strict'
import { overallTone, rowsFromHealth, unreachableRows } from '../src/health/healthModel.js'

const byKey = rows => Object.fromEntries(rows.map(row => [row.key, row]))

test('shows one row per service, all operational when every service passes', () => {
  const rows = rowsFromHealth({
    gateway: { status: 'pass' },
    'vla-manager': { status: 'pass' },
    processing: { status: 'pass' },
    'vc-manager': { status: 'pass' }
  }, 30.4)

  assert.deepEqual(rows.map(row => row.key), ['gateway', 'vla-manager', 'processing', 'vc-manager'])
  assert.ok(rows.every(row => row.status === 'operational' && row.detail === null))
  assert.equal(byKey(rows).gateway.latency, '30 ms')
  assert.equal(overallTone(rows), 'healthy')
})

test('maps warn and fail, and keeps the reason', () => {
  const rows = byKey(rowsFromHealth({
    gateway: { status: 'pass' },
    'vla-manager': { status: 'warn', output: 'data is kept in memory' },
    processing: { status: 'pass' },
    'vc-manager': { status: 'fail', output: 'postgres: timed out' }
  }, 10))

  assert.equal(rows['vla-manager'].status, 'degraded')
  assert.equal(rows['vla-manager'].detail, 'data is kept in memory')
  assert.equal(rows['vc-manager'].status, 'unavailable')
  assert.equal(rows['vc-manager'].detail, 'postgres: timed out')
  assert.equal(overallTone(Object.values(rows)), 'degraded')
})

test('a service the gateway leaves out is unavailable', () => {
  const rows = byKey(rowsFromHealth({ gateway: { status: 'pass' } }, 10))

  assert.equal(rows.processing.status, 'unavailable')
  assert.match(rows.processing.detail, /not reported/i)
})

test('an unreachable gateway makes every service unavailable', () => {
  const rows = unreachableRows()

  assert.ok(rows.every(row => row.status === 'unavailable'))
  assert.equal(overallTone(rows), 'degraded')
})
