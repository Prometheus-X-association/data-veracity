import http from 'http'

http
  .request({
    hostname: 'localhost',
    port: 80,
    path: '/ping',
    method: 'GET'
  }, (res) => {
    console.log(res)
    process.exit(res.statusCode === 200 ? 0 : 1)
  })
  .on('error', (_err) => process.exit(1))
  .end()
