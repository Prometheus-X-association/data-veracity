import { v4 as uuid } from 'uuid'

export async function addRoutes (app) {
  console.log('Mock server: no actual MongoDB connection')

  app.get('/api/vla', async (req, res) => {
    console.log('Serving dummy VLA documents')
    res.json(vlas)
  })

  app.post('/api/vla/from-fragments', async (req, res) => {
    const fragments = req.body
    console.log(`Got ${fragments.length} fragments in request`)

    const vla = {
      apiVersion: 'v3.0.1',
      dataProduct: 'test',
      id: uuid(),
      kind: 'DataContract',
      name: 'test',
      schema: [
        {
          logicalType: 'object',
          quality: [...fragments]
        }
      ],
      status: 'active',
      version: '1.0.0'
    }
    console.log('Assembled VLA:')
    console.log(vla)

    vlas.push(vla)
    console.log('Pushed VLA to local in-memory database')
  })
}

const vlas = [
  {
    apiVersion: 'v3.0.1',
    dataProduct: 'test',
    id: uuid(),
    kind: 'DataContract',
    name: 'test',
    schema: [
      {
        logicalType: 'object',
        quality: [
          {
            data_quality_type: 'custom',
            engine: 'schema',
            implementation: 'https://w3id.org/xapi/lms'
          }
        ]
      }
    ],
    status: 'active',
    version: '1.0.0'
  },
  {
    apiVersion: 'v3.0.1',
    dataProduct: 'test',
    id: uuid(),
    kind: 'DataContract',
    name: 'test',
    schema: [
      {
        logicalType: 'object',
        quality: [
          {
            data_quality_type: 'custom',
            engine: 'jq',
            implementation: "if [.verb.id] | inside(['https://w3id.org/xapi/netc/verbs/access        ed', 'https://w3id.org/xapi/netc/verbs/reviewed']) then 'Verb is in allowlist' else error('Verb i        s not allowed') end"
          }
        ]
      }
    ],
    status: 'active',
    version: '1.0.0'
  }
]
