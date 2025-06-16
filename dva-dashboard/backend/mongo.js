import mongoose from 'mongoose'

const MONGO_URL = process.env.DVA_MONGODB_URL || 'mongodb://localhost:27017'
const MONGO_DB = process.env.DVA_MONGODB_DB || 'dva'
const MONGO_COLLECTION = process.env.DVA_MONGODB_COLLECTION_REQUESTS || 'requests'

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
}
