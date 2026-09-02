import { attestationFailureScenarios, verificationFailureScenarios } from './failures/demoFailures.js'

const participants = ['Acme Analytics', 'Northwind Logistics', 'Contoso Energy']

const vla = (id, name, description, reference, tags) => ({
  id,
  name,
  description,
  dataReference: reference,
  participants,
  tags
})

export const demoVLAs = [
  vla('vla-quality-001', 'Real-time logistics telemetry', 'Validated shipment and vehicle telemetry exchanged between logistics partners.', 'fleet/telemetry/v3', ['logistics', 'real-time', 'telemetry']),
  vla('vla-energy-002', 'Renewable energy production', 'Hourly production readings with freshness, range, and schema guarantees.', 'energy/production/hourly', ['energy', 'sustainability', 'hourly']),
  vla('vla-learning-003', 'Learning activity stream', 'Learning events checked for schema compliance and privacy-safe identifiers.', 'learning/xapi/events', ['education', 'xAPI', 'privacy']),
  vla('vla-finance-004', 'Financial risk indicators', 'Risk indicators with signed provenance and bounded numerical values.', 'finance/risk/indicators', ['finance', 'risk', 'regulated']),
  vla('vla-health-005', 'Clinical trial observations', 'Clinical observations exchanged with strict completeness and timestamp rules.', 'clinical/trials/observations', ['health', 'clinical', 'high-assurance'])
]

const payloads = [
  { shipmentId: 'SHP-2026-0841', temperature: 4.2, humidity: 48, location: 'Budapest DC', timestamp: '2026-08-13T08:42:11Z' },
  { shipmentId: 'SHP-2026-0842', temperature: 5.1, humidity: 51, location: 'Vienna Hub', timestamp: '2026-08-13T08:37:04Z' },
  { meterId: 'MTR-HU-8831', productionKwh: 1842.6, renewableShare: 0.94, timestamp: '2026-08-13T08:00:00Z' },
  { meterId: 'MTR-DE-1044', productionKwh: 2291.1, renewableShare: 0.88, timestamp: '2026-08-13T08:00:00Z' },
  { actor: 'learner-2048', verb: 'completed', activity: 'secure-data-basics', score: 0.96, timestamp: '2026-08-13T07:58:31Z' },
  { actor: 'learner-3190', verb: 'passed', activity: 'privacy-by-design', score: 0.89, timestamp: '2026-08-13T07:51:10Z' },
  { portfolio: 'EU-ALPHA-07', riskScore: 0.27, confidence: 0.93, modelVersion: 'risk-4.2.1', timestamp: '2026-08-13T07:40:00Z' },
  { portfolio: 'EU-BETA-12', riskScore: 0.64, confidence: 0.87, modelVersion: 'risk-4.2.1', timestamp: '2026-08-13T07:35:00Z' },
  { subjectId: 'SUBJ-4408', visit: 'week-12', observationCount: 18, completeness: 1, timestamp: '2026-08-13T07:20:00Z' },
  { subjectId: 'SUBJ-4412', visit: 'week-12', observationCount: 17, completeness: 0.94, timestamp: '2026-08-13T07:15:00Z' }
]

const demoRequestStatuses = ['failed', 'pending', 'passed', 'failed', 'pending', 'failed', 'failed', 'failed', 'passed', 'failed', 'failed', 'failed', 'pending', 'failed', 'failed', 'passed']
const demoPresentationStatuses = ['verified', 'failed', 'pending', 'pending', 'failed', 'verified', 'failed', 'verified', 'failed', 'verified', 'pending', 'failed']

const makeRequest = (index, passing) => {
  const vlaIndex = index % demoVLAs.length
  const timestamp = new Date(Date.now() - index * 17 * 60 * 1000).toISOString()
  const status = demoRequestStatuses[index]
  const pending = status === 'pending'
  const failure = passing || pending ? null : attestationFailureScenarios[index % attestationFailureScenarios.length]
  return {
    requestID: `req-demo-${String(index + 1).padStart(3, '0')}`,
    type: index % 4 === 0 ? 'pov' : 'aov',
    exchangeID: `exchange-demo-${String(index + 1).padStart(3, '0')}`,
    contractID: `contract-${String(vlaIndex + 1).padStart(3, '0')}`,
    vlaID: demoVLAs[vlaIndex].id,
    receivedDate: timestamp,
    evaluationDate: pending ? null : new Date(new Date(timestamp).getTime() + 1800 * 1000).toISOString(),
    vcIssuedDate: passing ? new Date(new Date(timestamp).getTime() + 2100 * 1000).toISOString() : null,
    vcID: passing ? `vc-aov-demo-${String(index + 1).padStart(3, '0')}` : null,
    attesterID: participants[(index + 1) % participants.length],
    evaluationPassing: pending ? null : passing,
    status,
    failureCode: pending ? 'EVALUATION_PENDING' : failure?.code || null,
    failureStage: pending ? 'Processing' : failure?.stage || null,
    failureReason: pending ? 'The request is waiting for the evaluation processor.' : failure?.reason || null,
    failureEvidence: pending ? 'No evaluation result has been written yet.' : failure?.evidence || null,
    recommendedAction: pending ? 'Refresh after processing completes.' : failure?.action || null,
    failureRetryable: pending ? true : failure?.retryable ?? false,
    data: payloads[index % payloads.length],
    evaluationResults: JSON.stringify({
      schemaValid: passing,
      freshnessMinutes: 17 + index,
      qualityScore: passing ? 0.91 + (index % 7) / 100 : 0.42,
      checks: passing ? ['schema', 'freshness', 'range', 'provenance'] : ['schema', 'freshness'],
      failureCode: pending ? 'EVALUATION_PENDING' : failure?.code || null,
      failureReason: pending ? 'The request is waiting for the evaluation processor.' : failure?.reason || null,
      failureEvidence: pending ? 'No evaluation result has been written yet.' : failure?.evidence || null,
      recommendedAction: pending ? 'Refresh after processing completes.' : failure?.action || null
    })
  }
}

export const demoRequests = Array.from({ length: 16 }, (_, index) => makeRequest(index, demoRequestStatuses[index] === 'passed'))

const makePresentation = (index) => {
  const request = demoRequests[index % demoRequests.length]
  const payload = JSON.stringify(request.data)
  const status = demoPresentationStatuses[index]
  const verified = status === 'verified'
  const pending = status === 'pending'
  const failure = verified || pending ? null : verificationFailureScenarios[index % verificationFailureScenarios.length]
  return {
    thread_id: `verification-demo-${String(index + 1).padStart(3, '0')}`,
    created_at: request.receivedDate,
    updated_at: pending ? null : request.evaluationDate,
    role: index % 2 ? 'verifier' : 'prover',
    verified: pending ? null : verified,
    status,
    failureCode: pending ? 'VERIFICATION_PENDING' : failure?.code || null,
    failureReason: pending ? verificationFailureScenarios[3].reason : failure?.reason || null,
    failureEvidence: pending ? verificationFailureScenarios[3].evidence : failure?.evidence || null,
    recommendedAction: pending ? verificationFailureScenarios[3].action : failure?.action || null,
    failureRetryable: pending ? true : failure?.retryable ?? false,
    by_format: {
      pres_request: { indy: { requested_attributes: { attr_data_exchange_id: { restrictions: [{ 'attr::data_exchange_id::value': request.exchangeID }] } } } },
      pres: { indy: { requested_proof: { revealed_attrs: {
        attr_subject: { raw: participants[index % participants.length] },
        attr_data_exchange_id: { raw: request.exchangeID },
        attr_contract_id: { raw: request.contractID },
        attr_vc_id: { raw: request.vcID || 'not-issued' },
        attr_issuer_id: { raw: participants[(index + 1) % participants.length] },
        attr_payload: { raw: payload }
      } } } }
    }
  }
}

export const demoPresentations = Array.from({ length: 12 }, (_, index) => makePresentation(index))

export const demoCredentials = Array.from({ length: 14 }, (_, index) => ({
  attrs: {
    vc_id: `vc-demo-${String(index + 1).padStart(3, '0')}`,
    subject: participants[index % participants.length],
    data_exchange_id: `exchange-demo-${String((index % 10) + 1).padStart(3, '0')}`,
    contract_id: `contract-${String((index % 5) + 1).padStart(3, '0')}`,
    issuer_id: participants[(index + 1) % participants.length],
    issued_at: new Date(Date.now() - index * 3 * 60 * 60 * 1000).toISOString(),
    status: index % 8 === 0 ? 'revoked' : 'verified',
    failureCode: index % 8 === 0 ? 'CREDENTIAL_REVOKED' : null,
    failureReason: index % 8 === 0 ? 'The issuer revoked this credential after issuance.' : null,
    failureEvidence: index % 8 === 0 ? 'Credential status: revoked.' : null,
    recommendedAction: index % 8 === 0 ? 'Request a replacement credential.' : null,
    quality_score: (0.84 + (index % 15) / 100).toFixed(2)
  },
  schema_id: `schema:dva:quality:${(index % 5) + 1}`,
  credential_definition_id: `creddef:dva:demo:${(index % 3) + 1}`
}))
