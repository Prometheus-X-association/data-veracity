import cors from 'cors'
import express from 'express'

import { parseArgs } from 'node:util'

import { addRoutes as addMockRoutes } from './mock.js'
import { addRoutes as addMongoRoutes } from './mongo.js'

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

  const app = express()
  app.use(cors())
  app.use(express.json())

  if (mock) {
    await addMockRoutes(app)
  } else {
    await addMongoRoutes(app)
  }

  app.listen(3000, () => console.log('Listening on :3000'))
}
