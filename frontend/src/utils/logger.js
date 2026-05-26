const MAX_LOGS = 500

let logs = []
let listeners = []
let idCounter = 0

function notify() {
  listeners.forEach(fn => fn([...logs]))
}

export function getLogs() {
  return [...logs]
}

export function subscribe(fn) {
  listeners.push(fn)
  return () => {
    listeners = listeners.filter(l => l !== fn)
  }
}

export function clearLogs() {
  logs = []
  notify()
}

function addLog(entry) {
  const log = {
    id: ++idCounter,
    timestamp: new Date().toISOString(),
    ...entry,
  }
  logs.push(log)
  if (logs.length > MAX_LOGS) {
    logs = logs.slice(-MAX_LOGS)
  }
  notify()
  return log
}

export function logRequest(method, url, data) {
  return addLog({
    type: 'request',
    method: method.toUpperCase(),
    url,
    data,
  })
}

export function logResponse(method, url, status, data, duration) {
  return addLog({
    type: 'response',
    method: method.toUpperCase(),
    url,
    status,
    data,
    duration,
  })
}

export function logError(method, url, error, duration) {
  return addLog({
    type: 'error',
    method: method.toUpperCase(),
    url,
    status: error?.response?.status ?? '--',
    data: error?.response?.data ?? error?.message ?? String(error),
    duration,
  })
}
