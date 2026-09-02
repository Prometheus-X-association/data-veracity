import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const compose = readFileSync('test-env/compose.yml', 'utf8')
const common = readFileSync('test-env/common-services.yml', 'utf8')

test('runs the refactored stack without RabbitMQ', () => {
  assert.doesNotMatch(compose, /rabbit/i)
  assert.doesNotMatch(common, /rabbit/i)
  assert.doesNotMatch(compose, /--no-rmq/)
})

test('starts the APIs required by the frontend', () => {
  assert.match(compose, /^  vla-manager-api:/m)
  assert.match(compose, /^  dva-vc-manager:/m)
  assert.match(compose, /VLA_MANAGER_API_URL: http:\/\/vla-manager-api:8000/)
  assert.match(compose, /VC_MANAGER_API_URL: http:\/\/dva-vc-manager:8000/)
})
