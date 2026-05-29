import axios from 'axios'

const api = axios.create({
  baseURL: '',
  timeout: 120000,
})

export const calculateSchedule = (params, config) =>
  api.post('/api/schedule', { params, config }).then(r => r.data)

export const calculateScheduleByPlan = (deliveryPlanId, config) =>
  api.post('/api/schedule/by-plan', { delivery_plan_id: deliveryPlanId, config }).then(r => r.data)

export const validateParams = (params, config) =>
  api.post('/api/validate', { params, config }).then(r => r.data)

export const listProducts = () =>
  api.get('/api/lines/products').then(r => r.data)

export const createProduct = (data) =>
  api.post('/api/lines/products', data).then(r => r.data)

export const updateProduct = (id, data) =>
  api.put(`/api/lines/products/${id}`, data).then(r => r.data)

export const deleteProduct = (id) =>
  api.delete(`/api/lines/products/${id}`).then(r => r.data)

export const listLines = () =>
  api.get('/api/lines').then(r => r.data)

export const createLine = (data) =>
  api.post('/api/lines', data).then(r => r.data)

export const deleteLine = (id) =>
  api.delete(`/api/lines/${id}`).then(r => r.data)

export const listDeliveryPlans = () =>
  api.get('/api/delivery-plans').then(r => r.data)

export const getDeliveryPlan = (id) =>
  api.get(`/api/delivery-plans/${id}`).then(r => r.data)

export const createDeliveryPlan = (data) =>
  api.post('/api/delivery-plans', data).then(r => r.data)

export const deleteDeliveryPlan = (id) =>
  api.delete(`/api/delivery-plans/${id}`).then(r => r.data)

export const scheduleExport = async (result, planInfo) => {
  const response = await api.post('/api/schedule/export', {
    result,
    plan_info: planInfo,
  }, { responseType: 'blob' })
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', '排产结果.xlsx')
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}
