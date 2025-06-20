export async function addRoutes (app) {
  console.log('Mock server: no actual MongoDB connection')

  app.get('/api/requests', async (req, res) => {
    console.log('Serving dummy MongoDB request documents')
    res.json(requests)
  })

  app.get('/api/presentations', async (req, res) => {
    console.log('Serving dummy MongoDB presentation documents')
    res.json(presentations)
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

const presentations = [
  {
    state: 'done',
    created_at: '2025-06-20T13:56:33.026042Z',
    updated_at: '2025-06-20T13:56:36.026966Z',
    trace: false,
    pres_ex_id: 'f6a55376-6d57-4ba9-acdb-d9093e014a95',
    connection_id: '035b9506-7346-453d-8b6e-5de091746aef',
    thread_id: '3f18b204-25a0-4471-8828-7cc512805176',
    initiator: 'external',
    role: 'prover',
    pres_request: {
      '@type': 'https://didcomm.org/present-proof/2.0/request-presentation',
      '@id': '3f18b204-25a0-4471-8828-7cc512805176',
      will_confirm: true,
      formats: [{ attach_id: 'indy', format: 'hlindy/proof-req@v2.0' }],
      'request_presentations~attach': [
        {
          '@id': 'indy',
          'mime-type': 'application/json',
          data: {
            base64: '[skipped]'
          }
        }
      ]
    },
    pres: {
      '@type': 'https://didcomm.org/present-proof/2.0/presentation',
      '@id': '1b8b7c3e-de87-4afc-88ae-0541f2616e66',
      formats: [{ attach_id: 'indy', format: 'hlindy/proof@v2.0' }],
      'presentations~attach': [
        {
          '@id': 'indy',
          'mime-type': 'application/json',
          data: {
            base64: '[skipped]'
          }
        }
      ]
    },
    by_format: {
      pres_request: {
        indy: {
          name: 'AoVPresentationRequest',
          version: '1.0',
          requested_attributes: {
            attr_subject: {
              name: 'subject',
              restrictions: [{}]
            },
            attr_issuer_id: {
              name: 'issuer_id',
              restrictions: [{}]
            },
            attr_vc_id: {
              name: 'vc_id',
              restrictions: [{}]
            },
            attr_valid_since: {
              name: 'valid_since',
              restrictions: [{}]
            },
            attr_record_id: {
              name: 'record_id',
              restrictions: [{}]
            },
            attr_contract_id: {
              name: 'contract_id',
              restrictions: [{}]
            },
            attr_data_exchange_id: {
              name: 'data_exchange_id',
              restrictions: [
                {
                  'attr::data_exchange_id::value': 'xchg-0001'
                }
              ]
            },
            attr_payload: {
              name: 'payload',
              restrictions: [{}]
            }
          },
          requested_predicates: {},
          nonce: '195058371058392182808119'
        }
      },
      pres: {
        indy: {
          proof: {
            proofs: [
              {
                primary_proof: {
                  eq_proof: {
                    revealed_attrs: {
                      contract_id: '60520265233116485914036984123593989402100510890364900187590538684003136307526',
                      data_exchange_id: '41564896900366625241145769844496904708598445481231465005393477058023347902712',
                      issuer_id: '82947074037818567342427870253073249018696251143557230945081916676525930046016',
                      payload: '31663041503904792856986765859225621063225558270325784821780035322900769483950',
                      record_id: '5661194442212113697945542505938637080725489975915767275362107651365684438190',
                      subject: '74374528437247935297057485593980714204063542172420273025324246934417157983577',
                      valid_since: '85168353310612851534089439789050756401917246860463134894661291633256609375625',
                      vc_id: '58912764378088188130758772398456640451945394994014158922676057158193510400069'
                    },
                    a_prime: '[skipped]',
                    e: '[skipped]',
                    v: '[skipped]',
                    m: {
                      master_secret: '[skipped]'
                    },
                    m2: '[skipped]'
                  },
                  ge_proofs: []
                },
                non_revoc_proof: null
              }
            ],
            aggregated_proof: {
              c_hash: '22230490762546210622345195096307420714149779272654564099112614393996469235660',
              c_list: [[1, 2, 3]]
            }
          },
          requested_proof: {
            revealed_attrs: {
              attr_record_id: {
                sub_proof_index: 0,
                raw: '44e78d63-01dc-4a9a-a4b1-0abd3f005b45',
                encoded: '5661194442212113697945542505938637080725489975915767275362107651365684438190'
              },
              attr_payload: {
                sub_proof_index: 0,
                raw: '{"success": true, "results": {"success": true, "expectation_config": {"type": "expect_column_values_to_be_between", "kwargs": {"batch_id": "test_src-test_asset", "column": "timestamp", "min_value": "2025-01-01T00:00:00+00:00", "max_value": "2026-01-01T00:00:00+00:00"}, "meta": {}}, "result": {"element_count": 1, "unexpected_count": 0, "unexpected_percent": 0.0, "partial_unexpected_list": [], "missing_count": 0, "missing_percent": 0.0, "unexpected_percent_total": 0.0, "unexpected_percent_nonmissing": 0.0, "partial_unexpected_counts": [], "partial_unexpected_index_list": []}, "meta": {}, "exception_info": {"raised_exception": false, "exception_traceback": null, "exception_message": null}}}',
                encoded: '31663041503904792856986765859225621063225558270325784821780035322900769483950'
              },
              attr_valid_since: {
                sub_proof_index: 0,
                raw: '2025-06-20T13:56:14.927161',
                encoded: '85168353310612851534089439789050756401917246860463134894661291633256609375625'
              },
              attr_subject: {
                sub_proof_index: 0,
                raw: '/catalog/participants/provider-test-id',
                encoded: '74374528437247935297057485593980714204063542172420273025324246934417157983577'
              },
              attr_data_exchange_id: {
                sub_proof_index: 0,
                raw: 'xchg-0001',
                encoded: '41564896900366625241145769844496904708598445481231465005393477058023347902712'
              },
              attr_contract_id: {
                sub_proof_index: 0,
                raw: 'contract-00001',
                encoded: '60520265233116485914036984123593989402100510890364900187590538684003136307526'
              },
              attr_vc_id: {
                sub_proof_index: 0,
                raw: 'c4431599-2648-4cfe-ada5-a0f81d67dbd6',
                encoded: '58912764378088188130758772398456640451945394994014158922676057158193510400069'
              },
              attr_issuer_id: {
                sub_proof_index: 0,
                raw: 'attester-0000',
                encoded: '82947074037818567342427870253073249018696251143557230945081916676525930046016'
              }
            },
            self_attested_attrs: {},
            unrevealed_attrs: {},
            predicates: {}
          },
          identifiers: [
            {
              schema_id: '6utUyTDnDBPsFo9HrQDUyg:2:Self-Identity-4f6f46:1.0',
              cred_def_id: '6utUyTDnDBPsFo9HrQDUyg:3:CL:2844613:self-identity',
              rev_reg_id: null,
              timestamp: null
            }
          ]
        }
      }
    },
    auto_present: true,
    auto_verify: false,
    auto_remove: false
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
