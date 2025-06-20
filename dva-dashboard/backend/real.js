import axios from 'axios'
import mongoose from 'mongoose'

const MONGO_URL = process.env.DVA_MONGODB_URL || 'mongodb://localhost:27017'
const MONGO_DB = process.env.DVA_MONGODB_DB || 'dva'
const MONGO_COLLECTION = process.env.DVA_MONGODB_COLLECTION_REQUESTS || 'requests'

const ACAPY_URL = process.env.DVA_ACA_PY_URL || 'http://localhost:8030'

export async function addRoutes (app) {
  console.log('Attempting to connect to mongodb...')
  const conn = await mongoose.connect(`${MONGO_URL}/${MONGO_DB}`)
  const coll = conn.model('Requests', {}, MONGO_COLLECTION)
  console.log('MongoDB connected')

  app.get('/api/requests', async (req, res) => {
    console.log('Serving all MongoDB request documents')
    const docs = await coll.find().sort('-receivedDate')
    res.json(docs)
  })

  app.get('/api/presentations', async (req, res) => {
    console.log('Serving all presentations')
    const response = await axios.get(`${ACAPY_URL}/present-proof-2.0/records`)
    res.json(response.data.results)
  })

  app.get('/api/credentials', async (req, res) => {
    console.log('Serving all verifiable credentials')
    const response = await axios.get(`${ACAPY_URL}/credentials`)
    res.json(response.data.results)
  })
}
