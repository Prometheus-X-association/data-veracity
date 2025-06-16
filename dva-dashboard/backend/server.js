import cors from 'cors'
import express from 'express'
import mongoose from 'mongoose'

import { parseArgs } from 'node:util'

const MONGO_URL = process.env.DVA_MONGODB_URL || 'mongodb://localhost:27017'
const MONGO_DB = process.env.DVA_MONGODB_DB || 'dva'
const MONGO_COLLECTION = process.env.DVA_MONGODB_COLLECTION_REQUESTS || 'requests'

main().catch(err => console.log(err))

async function main () {
  const { values: { mock } } = parseArgs({
    options: {
      mock: {
        type: 'boolean',
        short: 'm'
      }
    }
  })

  if (mock) {
    await serveMock()
  } else {
    await serveFromMongo()
  }
}

async function serveFromMongo () {
  console.log('Attempting to connect to mongodb...')
  const conn = await mongoose.connect(`${MONGO_URL}/${MONGO_DB}`)
  const coll = conn.model('Requests', {}, MONGO_COLLECTION)
  console.log('MongoDB connected')

  const app = express()
  app.use(cors())
  app.use(express.json())

  app.get('/api/requests', async (req, res) => {
    console.log('Serving all MongoDB request documents')
    const docs = await coll.find().sort('-receivedDate')
    res.json(docs)
  })

  app.listen(3000, () => console.log('Listening on :3000'))
}

async function serveMock () {
  console.log('Mock server: no actual MongoDB connection')

  const app = express()
  app.use(cors())
  app.use(express.json())

  app.get('/api/requests', async (req, res) => {
    console.log('Serving dummy MongoDB request documents')
    const docs = [
      {
        _id: '684ee8c24c20fe1aaed81516',
        type: 'pov',
        requestID: '7fb48b3b-a905-480a-aa17-864a09df6e58',
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
    res.json(docs)
  })

  app.listen(3000, () => console.log('Listening on :3000'))
}
