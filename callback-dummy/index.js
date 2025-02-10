'use strict'

import hapi from '@hapi/hapi'
import pino from 'pino'

const logger = pino()

const host = process.env.CALLBACK_DUMMY_HOST || 'localhost'
const port = process.env.CALLBACK_DUMMY_PORT || 9098

const reqs = []

const init = async () => {
  const server = hapi.server({ port, host })

  server.route([
    {
      method: '*',
      path: '/callback/{any*}',
      handler: (req, h) => {
        const idx = reqs.push({
          headers: req.headers,
          method: req.method,
          mime: req.mime,
          params: req.params,
          path: req.path,
          payload: req.payload,
        })

        logger.info(
          { path: req.path, method: req.method, idx },
          `Received ${req.method} request to ${req.path}; saving data`,
        )

        return { index: idx }
      },
    },
    {
      method: 'GET',
      path: '/get/{index}',
      handler: (req, h) => {
        let idx = req.params.index
        if (idx === 'last') idx = -1

        logger.info(
          { idx },
          `Received request to retrieve request ${idx}`,
        )

        const r = reqs.at(idx)
	if (r === undefined) {
	  logger.warning(`Requested request at index ${idx} does not exist`)
	  return h.response().code(404)
	} else {
	  return h.response(r)
	}
      },
    },
    {
      method: '*',
      path: '/{any*}',
      handler: (req, h) => {
        logger.info(
          { path: req.path },
          `Received request to unhandled path ${req.path}`,
        )
        return h.response().code(404)
      },
    },
  ])

  await server.start()
  logger.info(`Server listening on ${host}:${port}`)
}

process.on('unhandledRejection', (err) => {
  logger.error(err)
  process.exit(1)
})

init()
