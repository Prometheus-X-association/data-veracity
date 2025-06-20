export async function addRoutes (app) {
  console.log('Mock server: no actual MongoDB connection')

  app.get('/api/requests', async (req, res) => {
    console.log('Serving dummy MongoDB request documents')
    res.json(requests)
  })

  app.get('/api/credentials', async (req, res) => {
    console.log('Serving dummy VCs')
    res.json(credentials)
  })
}

const requests = [
  {
    _id: '684ee8c24c20fe1aaed81516',
    type: 'pov',
    requestID: '7fb48b3b-a905-480a-aa17-864a09df6e58',
    exchangeID: 'a298bdc1-0157-4621-a79a-e36aa94a7d3f',
    contractID: '39dc6fbd-3da4-46b9-958a-a40be637f2a5',
    vlaID: '2e99b60d-8cf7-4668-a234-96ebfd6a2b63',
    data: [1, 2, 3],
    attesterID: 'attester-1821',
    evaluationPassing: false,
    evaluationResults: '{"success": false, "expectation_config": {"type": "expect_column_values_to_be_between", "kwargs": {"column": "timestamp", "min_value": "2025-01-01T00:00:00+00:00", "max_value": "2026-01-01T00:00:00+00:00", "batch_id": "test_src-test_asset"}, "meta": {}}}',
    receivedDate: '2025-06-15T15:37:38.644Z',
    evaluationDate: '2025-06-15T15:37:38.887Z',
    vcIssuedDate: '2025-06-15T15:37:39.688Z',
    vcID: 'd07feb0f-fc14-4cb8-98e5-c1b42e45fd22'
  },
  {
    _id: '684ee8c24c20fe1aaed81517',
    type: 'aov',
    requestID: '67c588c9-e76b-4046-8c94-c4c5e1139f0a',
    exchangeID: '4aa41227-8c4e-40bf-b351-09f5977d803e',
    contractID: '235ba03a-5387-44c5-af0b-ff72667d1fb0',
    vlaID: '27673009-a9a4-4223-8928-ac3eba1dd4d2',
    data: [9, 9, 9],
    attesterID: 'attester-0010',
    evaluationPassing: true,
    evaluationResults: '{"success": true, "jq_result": "ok"}',
    receivedDate: '2025-06-12T15:37:38.644Z',
    evaluationDate: '2025-06-12T15:37:38.887Z',
    vcIssuedDate: '2025-06-12T15:37:39.688Z',
    vcID: '2c0f65ab-cfff-45ef-832d-f0337a7881ec'
  }
]

const credentials = [
  {
    referent: '63f9947a-b108-4bdf-bcca-c987719299f3',
    schema_id: '6utUyTDnDBPsFo9HrQDUyg:2:Self-Identity-c28a98:1.0',
    cred_def_id: '6utUyTDnDBPsFo9HrQDUyg:3:CL:2839410:self-identity',
    rev_reg_id: null,
    cred_rev_id: null,
    attrs: {
      record_id: '3cce1fa6-671d-4c03-9c8a-801a15c21ae5',
      valid_since: '2025-06-16T10:05:54.341346',
      subject: '/catalog/participants/provider-test-id',
      issuer_id: 'attester-0000',
      contract_id: '5e9e1c9fefc047c9b815053d62189222',
      data_exchange_id: '210b1487dea64fbf9204852df486f3e1',
      vc_id: 'd488dc7f-6fa7-4f0a-b82d-ea08cd9881be',
      payload: '{"success": false, "results": {"success": false, "expectation_config": {"type": "expect_column_values_to_be_between", "kwargs": {"column": "timestamp", "min_value": "2025-01-01T00:00:00+00:00", "max_value": "2026-01-01T00:00:00+00:00", "batch_id": "test_src-test_asset"}, "meta": {}}, "result": {}, "meta": {}, "exception_info": "[skipped]"}}'
    }
  }
]
