import mongoose from 'mongoose'
import { v4 as uuid } from 'uuid'

const MONGO_URL = process.env.DVA_MONGODB_URL || 'mongodb://localhost:27017'
const MONGO_DB = process.env.DVA_MONGODB_DB || 'dva'
const MONGO_COLLECTION = process.env.DVA_MONGODB_COLLECTION_REQUESTS || 'vlas'

export async function addRoutes (app) {
  console.log('Attempting to connect to mongodb...')
  const conn = await mongoose.connect(`${MONGO_URL}/${MONGO_DB}`)
  const coll = conn.model('VLAs', {}, MONGO_COLLECTION)
  console.log('MongoDB connected')

  app.get('/api/vla', async (req, res) => {
    console.log('Serving all known VLAs from MongoDB')
    const docs = await coll.find()
    res.json(docs)
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

    await coll.create(vla)
  })
}
