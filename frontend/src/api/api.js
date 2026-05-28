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

export async function calculateScheduleByPlan(deliveryPlanId, config = {}) {
  const response = await request.post('/api/schedule/by-plan', {
    delivery_plan_id: deliveryPlanId,
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

export async function listProducts() {
  const response = await request.get('/api/lines/products')
  return response.data
}

export async function createProduct(data) {
  const response = await request.post('/api/lines/products', data)
  return response.data
}

export async function updateProduct(id, data) {
  const response = await request.put(`/api/lines/products/${id}`, data)
  return response.data
}

export async function deleteProduct(id) {
  const response = await request.delete(`/api/lines/products/${id}`)
  return response.data
}

export async function listLines() {
  const response = await request.get('/api/lines')
  return response.data
}

export async function createLine(data) {
  const response = await request.post('/api/lines', data)
  return response.data
}

export async function deleteLine(id) {
  const response = await request.delete(`/api/lines/${id}`)
  return response.data
}

export async function listDeliveryPlans() {
  const response = await request.get('/api/delivery-plans')
  return response.data
}

export async function getDeliveryPlan(id) {
  const response = await request.get(`/api/delivery-plans/${id}`)
  return response.data
}

export async function createDeliveryPlan(data) {
  const response = await request.post('/api/delivery-plans', data)
  return response.data
}

export async function deleteDeliveryPlan(id) {
  const response = await request.delete(`/api/delivery-plans/${id}`)
  return response.data
}

export const scheduleExport = async (result, planInfo) => {
  const res = await request.post('/api/schedule/export', { result, plan_info: planInfo }, { responseType: 'blob' })
  const url = window.URL.createObjectURL(new Blob([res.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', '排产结果.xlsx')
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}
