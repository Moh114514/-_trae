import axios from 'axios'
import { ElMessage } from 'element-plus'

const stripTrailingSlashes = (value = '') => value.replace(/\/+$/, '')

const resolveApiBaseURL = () => {
  const envBase = (import.meta.env.VITE_API_BASE_URL || '').trim()
  if (envBase) {
    return `${stripTrailingSlashes(envBase)}/api`
  }

  if (typeof window === 'undefined') {
    return '/api'
  }

  const runtimeBase = (typeof window.__BEIMS_API_BASE__ === 'string' ? window.__BEIMS_API_BASE__ : '').trim()
  if (runtimeBase) {
    return `${stripTrailingSlashes(runtimeBase)}/api`
  }

  const { hostname, host, protocol, port } = window.location
  const isLocalHost = hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1'
  const isTunnelHost = host.includes('ngrok') || host.includes('trycloudflare.com')

  if (isTunnelHost) {
    return `${protocol}//${host}/api`
  }

  if (isLocalHost && port !== '8001') {
    return 'http://localhost:8001/api'
  }

  return '/api'
}

const resolvedApiBaseURL = resolveApiBaseURL()

const api = axios.create({
  baseURL: resolvedApiBaseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

const authDebugEnabled = import.meta.env.VITE_AUTH_DEBUG !== 'false'

api.interceptors.request.use((config) => {
  if (authDebugEnabled && (config.url === '/auth/me' || config.url === '/auth/login')) {
    const token = localStorage.getItem('token')
    console.info('[AUTHDBG][request]', {
      method: config.method,
      url: config.url,
      hasToken: Boolean(token),
      tokenPrefix: token ? token.slice(0, 12) : null
    })
  }
  return config
})

api.interceptors.response.use(
  response => {
    if (authDebugEnabled && (response.config?.url === '/auth/me' || response.config?.url === '/auth/login')) {
      console.info('[AUTHDBG][response]', {
        method: response.config?.method,
        url: response.config?.url,
        status: response.status
      })
    }
    return response
  },
  error => {
    if (authDebugEnabled && (error.config?.url === '/auth/me' || error.config?.url === '/auth/login')) {
      console.error('[AUTHDBG][error]', {
        method: error.config?.method,
        url: error.config?.url,
        status: error.response?.status,
        detail: error.response?.data?.detail,
        message: error.message
      })
    }
    const message = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export const authAPI = {
  login: (username, password) => {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    params.append('grant_type', 'password')
    return api.post('/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
  },
  
  register: (userData) => api.post('/auth/register', userData),
  
  getCurrentUser: () => api.get('/auth/me', {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  }),
  
  getUsers: () => api.get('/auth/users', {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  })
}

export const isAuthenticated = () => {
  return localStorage.getItem('token') !== null
}

export const getToken = () => {
  return localStorage.getItem('token')
}

export const setToken = (token) => {
  localStorage.setItem('token', token)
}

export const removeToken = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

export const setUser = (user) => {
  localStorage.setItem('user', JSON.stringify(user))
}

export const getUser = () => {
  const userStr = localStorage.getItem('user')
  return userStr ? JSON.parse(userStr) : null
}
