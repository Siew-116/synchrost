import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Attach token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Redirect on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// --- Auth API ---
export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (data: any) =>
    api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
  updateMe: (data: any) => api.put('/auth/me', data),
}

// --- Academic API ---
export const academicAPI = {
  list: (params?: any) => api.get('/academic/', { params }),
  create: (data: any) => api.post('/academic/', data),
  get: (id: number) => api.get(`/academic/${id}`),
  update: (id: number, data: any) => api.put(`/academic/${id}`, data),
  delete: (id: number) => api.delete(`/academic/${id}`),
}

// --- Customers API ---
export const customerAPI = {
  list: () => api.get('/customers/'),
  create: (data: any) => api.post('/customers/', data),
  get: (id: number) => api.get(`/customers/${id}`),
  update: (id: number, data: any) => api.put(`/customers/${id}`, data),
  delete: (id: number) => api.delete(`/customers/${id}`),
}

// --- Products API ---
export const productAPI = {
  list: () => api.get('/products/'),
  create: (data: any) => api.post('/products/', data),
  get: (id: number) => api.get(`/products/${id}`),
  update: (id: number, data: any) => api.put(`/products/${id}`, data),
  delete: (id: number) => api.delete(`/products/${id}`),
  movements: (id: number) => api.get(`/products/${id}/movements`),
  lowStock: () => api.get('/products/alerts/low-stock'),
}

// --- Orders API ---
export const orderAPI = {
  list: (status?: string) => api.get('/orders/', { params: status ? { status_filter: status } : {} }),
  create: (data: any) => api.post('/orders/', data),
  get: (id: number) => api.get(`/orders/${id}`),
  update: (id: number, data: any) => api.put(`/orders/${id}`, data),
  history: (id: number) => api.get(`/orders/${id}/history`),
}

// --- Bulk Orders API ---
export const bulkOrderAPI = {
  list: () => api.get('/bulk-orders/'),
  create: (data: any) => api.post('/bulk-orders/', data),
  get: (id: number) => api.get(`/bulk-orders/${id}`),
  update: (id: number, data: any) => api.put(`/bulk-orders/${id}`, data),
  allocations: (id: number) => api.get(`/bulk-orders/${id}/allocations`),
  delete: (id: number) => api.delete(`/bulk-orders/${id}`),
}

// --- Suppliers API ---
export const supplierAPI = {
  list: () => api.get('/suppliers/'),
  create: (data: any) => api.post('/suppliers/', data),
  get: (id: number) => api.get(`/suppliers/${id}`),
  update: (id: number, data: any) => api.put(`/suppliers/${id}`, data),
  delete: (id: number) => api.delete(`/suppliers/${id}`),
}

// --- Exceptions API ---
export const exceptionAPI = {
  list: (status?: string) => api.get('/exceptions/', { params: status ? { status_filter: status } : {} }),
  create: (data: any) => api.post('/exceptions/', data),
  get: (id: number) => api.get(`/exceptions/${id}`),
  update: (id: number, data: any) => api.put(`/exceptions/${id}`, data),
  delete: (id: number) => api.delete(`/exceptions/${id}`),
}

// --- Finance API ---
export const financeAPI = {
  summary: () => api.get('/finance/summary'),
  transactions: () => api.get('/finance/transactions'),
}

// --- Dashboard API ---
export const dashboardAPI = {
  get: () => api.get('/dashboard/'),
}

// --- Agent API ---
export const agentAPI = {
  chat: (message: string, context?: string) => api.post('/agent/chat', { message, context }),
  logs: (limit?: number) => api.get('/agent/logs', { params: limit ? { limit } : {} }),
  tools: () => api.get('/agent/tools'),
}

// --- Automation API ---
export const automationAPI = {
  list: () => api.get('/automation/'),
  update: (id: number, data: any) => api.put(`/automation/${id}`, data),
  runNow: (id: number) => api.post(`/automation/${id}/run-now`),
  runs: (id: number) => api.get(`/automation/${id}/runs`),
}

// --- Messages API ---
export const messageAPI = {
  list: () => api.get('/messages/'),
  create: (data: any) => api.post('/messages/', data),
  approve: (id: number) => api.put(`/messages/${id}/approve`),
  markSent: (id: number) => api.put(`/messages/${id}/mark-sent`),
  delete: (id: number) => api.delete(`/messages/${id}`),
}

// --- Approvals API ---
export const approvalAPI = {
  list: (status?: string) => api.get('/approvals/', { params: status ? { status_filter: status } : {} }),
  decide: (id: number, approved: boolean, note?: string) =>
    api.put(`/approvals/${id}/decide`, { approved, note }),
}

// --- Notifications API ---
export const notificationAPI = {
  list: (unreadOnly?: boolean) => api.get('/notifications/', { params: unreadOnly ? { unread_only: true } : {} }),
  markRead: (id: number) => api.put(`/notifications/${id}/read`),
  markAllRead: () => api.put('/notifications/read-all'),
}

// --- Export API ---
export const exportAPI = {
  masterlist: () => api.get('/export/masterlist', { responseType: 'blob' }),
}
