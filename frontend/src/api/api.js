import axios from 'axios'
import { logRequest, logResponse, logError } from '../utils/logger'

const request = axios.create({
  baseURL: '',
  timeout: 120000,
})

request.interceptors.request.use((config) => {
  config._startTime = Date.now()
  logRequest(config.method, config.url, config.params || config.data)
  return config
})

request.interceptors.response.use(
  (response) => {
    const duration = Date.now() - (response.config._startTime || 0)
    logResponse(response.config.method, response.config.url, response.status, response.data, duration)
    return response
  },
  (error) => {
    const duration = error.config ? Date.now() - (error.config._startTime || 0) : 0
    const config = error.config || {}
    logError(config.method || 'unknown', config.url || 'unknown', error, duration)
    return Promise.reject(error)
  }
)

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

export const materialApi = {
  list: (params) => request.get('/api/materials', { params }).then(r => r.data),
  get: (id) => request.get(`/api/materials/${id}`).then(r => r.data),
  create: (data) => request.post('/api/materials', data).then(r => r.data),
  update: (id, data) => request.put(`/api/materials/${id}`, data).then(r => r.data),
  delete: (id) => request.delete(`/api/materials/${id}`).then(r => r.data),
}

export const bomApi = {
  list: (params) => request.get('/api/manufacture-boms', { params }).then(r => r.data),
  get: (id) => request.get(`/api/manufacture-boms/${id}`).then(r => r.data),
  create: (data) => request.post('/api/manufacture-boms', data).then(r => r.data),
  update: (id, data) => request.put(`/api/manufacture-boms/${id}`, data).then(r => r.data),
  delete: (id) => request.delete(`/api/manufacture-boms/${id}`).then(r => r.data),
}

export const processApi = {
  list: (params) => request.get('/api/processes', { params }).then(r => r.data),
  get: (id) => request.get(`/api/processes/${id}`).then(r => r.data),
  create: (data) => request.post('/api/processes', data).then(r => r.data),
  update: (id, data) => request.put(`/api/processes/${id}`, data).then(r => r.data),
  delete: (id) => request.delete(`/api/processes/${id}`).then(r => r.data),
}

export const processRouteApi = {
  list: (params) => request.get('/api/process-routes', { params }).then(r => r.data),
  get: (id) => request.get(`/api/process-routes/${id}`).then(r => r.data),
  create: (data) => request.post('/api/process-routes', data).then(r => r.data),
  update: (id, data) => request.put(`/api/process-routes/${id}`, data).then(r => r.data),
  delete: (id) => request.delete(`/api/process-routes/${id}`).then(r => r.data),
  validate: (data) => request.post('/api/process-routes/validate', data).then(r => r.data),
}

export const resourceApi = {
  list: (params) => request.get('/api/production-resources', { params }).then(r => r.data),
  get: (id) => request.get(`/api/production-resources/${id}`).then(r => r.data),
  create: (data) => request.post('/api/production-resources', data).then(r => r.data),
  update: (id, data) => request.put(`/api/production-resources/${id}`, data).then(r => r.data),
  delete: (id) => request.delete(`/api/production-resources/${id}`).then(r => r.data),
}

const calendarUrls = {
  work_pattern: '/api/work-modes',
  work_calendar: '/api/work-calendars',
  resource_calendar: '/api/resource-calendars',
}

export const calendarApi = {
  list: ({ type = 'work_calendar', ...params }) =>
    request.get(calendarUrls[type] || calendarUrls.work_calendar, { params })
      .then(r => {
        const items = Array.isArray(r.data) ? r.data : (r.data.items || [])
        return { items, total: items.length, page: 1, page_size: items.length }
      }),
  get: (id, type) =>
    request.get(`${calendarUrls[type] || calendarUrls.work_calendar}/${id}`).then(r => r.data),
  create: (data) => {
    const { type, ...payload } = data
    return request.post(calendarUrls[type] || calendarUrls.work_calendar, payload).then(r => r.data)
  },
  update: (id, data) => {
    const { type, ...payload } = data
    return request.put(`${calendarUrls[type] || calendarUrls.work_calendar}/${id}`, payload).then(r => r.data)
  },
  delete: (id, type) =>
    request.delete(`${calendarUrls[type] || calendarUrls.work_calendar}/${id}`).then(r => r.data),
}

export const incomingOrderApi = {
  list: (params) => request.get('/api/incoming-material-orders', { params }).then(r => r.data),
  get: (id) => request.get(`/api/incoming-material-orders/${id}`).then(r => r.data),
  create: (data) => request.post('/api/incoming-material-orders', data).then(r => r.data),
  update: (id, data) => request.put(`/api/incoming-material-orders/${id}`, data).then(r => r.data),
  delete: (id) => request.delete(`/api/incoming-material-orders/${id}`).then(r => r.data),
}

export const orderApi = {
  list: (params) => request.get('/api/production-orders', { params }).then(r => r.data),
  get: (id) => request.get(`/api/production-orders/${id}`).then(r => r.data),
  create: (data) => request.post('/api/production-orders', data).then(r => r.data),
  update: (id, data) => request.put(`/api/production-orders/${id}`, data).then(r => r.data),
  delete: (id) => request.delete(`/api/production-orders/${id}`).then(r => r.data),
  toggleCanSchedule: (id, data) => request.put(`/api/production-orders/${id}/can-schedule`, data).then(r => r.data),
}

export const strategyApi = {
  list: (params) => request.get('/api/planning-strategies', { params }).then(r => r.data),
  get: (id) => request.get(`/api/planning-strategies/${id}`).then(r => r.data),
  create: (data) => request.post('/api/planning-strategies', data).then(r => r.data),
  update: (id, data) => request.put(`/api/planning-strategies/${id}`, data).then(r => r.data),
  delete: (id) => request.delete(`/api/planning-strategies/${id}`).then(r => r.data),
  toggleActive: (id, data) => request.put(`/api/planning-strategies/${id}/active`, data).then(r => r.data),
  getRuleOptions: () => request.get('/api/planning-strategies/scheduling-rule/options').then(r => r.data),
}

export const smartSchedulingApi = {
  generate: (data) => request.post('/api/smart-scheduling/generate', data),
  getProgress: (taskId) => request.get('/api/smart-scheduling/plan/progress', { params: { task_id: taskId } }),
  confirm: () => request.post('/api/smart-scheduling/plan/pending/confirm'),
  cancel: () => request.post('/api/smart-scheduling/plan/pending/cancel'),
  clearPlan: () => request.post('/api/smart-scheduling/plan/clear'),
  previewTasks: (data) => request.post('/api/smart-scheduling/preview/plan/tasks', data),
  previewGantt: () => request.post('/api/smart-scheduling/preview/plan/resource/gantt'),
  getTasks: (params) => request.get('/api/smart-scheduling/plan/tasks', { params }).then(r => r.data),
  getGantt: (orderId) => request.post('/api/smart-scheduling/plan/resource/gantt', orderId ? { order_id: orderId } : {}).then(r => r.data),
}
