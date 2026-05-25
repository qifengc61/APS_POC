import axios from 'axios'

const request = axios.create({
  baseURL: '',
  timeout: 120000,
})

export async function calculateSchedule(params, config = {}) {
  const response = await request.post('/api/schedule', {
    params,
    config,
  })
  return response.data
}

export async function validateParams(params, config = {}) {
  const response = await request.post('/api/validate', {
    params,
    config,
  })
  return response.data
}
