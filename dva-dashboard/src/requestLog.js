// Maps one entry of the DVA API's `GET /info/requests` log to the record shape
// the dashboard components and `normalizeAttestationRecord` work with.
//
// The API attests synchronously: an entry is written once the request has been
// answered, so it is never "waiting for the processor".  The log carries
// `id` and `receivedDate`; entries that failed before an evaluation finished
// carry an `error` ({ title, detail }) and no evaluation results.
//
// Demo records already use the dashboard's own shape and pass through unchanged.
export function fromRequestLog (log = {}) {
  const evaluated = !log.error
  return {
    ...log,
    requestID: log.requestID ?? log.id,
    evaluationDate: log.evaluationDate ?? (evaluated ? log.receivedDate ?? null : null)
  }
}

export function fromRequestLogs (logs) {
  return Array.isArray(logs) ? logs.map(fromRequestLog) : []
}
