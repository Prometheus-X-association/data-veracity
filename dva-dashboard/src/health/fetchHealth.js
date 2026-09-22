import axios from 'axios'
import { HEALTH_ENDPOINT, rowsFromHealth, unreachableRows } from './healthModel.js'

export async function fetchHealthRows () {
  const started = performance.now()
  try {
    const response = await axios.get(HEALTH_ENDPOINT)
    return rowsFromHealth(response.data, performance.now() - started)
  } catch {
    return unreachableRows()
  }
}
