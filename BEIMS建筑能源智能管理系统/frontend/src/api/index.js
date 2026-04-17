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

const statsDebugEnabled = import.meta.env.VITE_STATS_DEBUG !== 'false'

const isStatisticsRequest = (config = {}) => {
  const url = config.url || ''
  return url.startsWith('/query/statistics/')
}

const summarizePayload = (data) => {
  if (data == null) return data
  if (Array.isArray(data)) return `array(len=${data.length})`
  if (typeof data === 'object') {
    return Object.keys(data).reduce((acc, key) => {
      const value = data[key]
      if (Array.isArray(value)) {
        acc[key] = `array(len=${value.length})`
      } else if (value && typeof value === 'object') {
        acc[key] = `object(keys=${Object.keys(value).length})`
      } else {
        acc[key] = value
      }
      return acc
    }, {})
  }
  return data
}

api.interceptors.request.use((config) => {
  if (statsDebugEnabled && isStatisticsRequest(config)) {
    config.metadata = { startTime: Date.now() }
    console.info('[STATDBG][frontend][request]', {
      method: config.method,
      url: config.url,
      params: summarizePayload(config.params),
      data: summarizePayload(config.data)
    })
  }
  return config
})

api.interceptors.response.use(
  response => {
    const { config } = response
    if (statsDebugEnabled && isStatisticsRequest(config)) {
      const elapsed = config?.metadata?.startTime ? Date.now() - config.metadata.startTime : null
      console.info('[STATDBG][frontend][response]', {
        method: config.method,
        url: config.url,
        status: response.status,
        elapsed_ms: elapsed,
        data: summarizePayload(response.data)
      })
    }
    return response
  },
  error => {
    const config = error.config || {}
    const isStats = isStatisticsRequest(config)
    if (statsDebugEnabled && isStatisticsRequest(config)) {
      const elapsed = config?.metadata?.startTime ? Date.now() - config.metadata.startTime : null
      console.error('[STATDBG][frontend][error]', {
        method: config.method,
        url: config.url,
        status: error.response?.status,
        elapsed_ms: elapsed,
        response: summarizePayload(error.response?.data),
        message: error.message
      })
    }
    const status = error.response?.status
    const detail = error.response?.data?.detail
    const likelyBackendUnavailable = isStats && (
      !error.response ||
      (status === 500 && !detail)
    )
    const message = likelyBackendUnavailable
      ? '统计服务不可用，请确认后端8001已启动并保持运行'
      : (detail || error.message || '请求失败')
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export const dataAPI = {
  importCSV: (formData) => api.post('/data/import/csv', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  
  importExcel: (formData) => api.post('/data/import/excel', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  
  getBuildings: () => api.get('/data/buildings'),
  
  getMeters: () => api.get('/data/meters'),
  
  getDateRange: (buildingId) => api.get('/data/date-range', { params: { building_id: buildingId } }),
  
  getSummary: () => api.get('/data/summary')
}

export const queryAPI = {
  queryData: (params) => api.post('/query/data', params),
  
  naturalLanguageQuery: (params) => api.post('/query/natural-language', params),
  
  timeAggregation: (params) => api.post('/query/statistics/time-aggregation', params),
  
  calculateCOP: (params) => api.post('/query/statistics/cop', params),
  
  detectAnomalies: (params) => api.post('/query/statistics/anomalies', params),
  
  getRanking: (params) => api.post('/query/statistics/ranking', params),
  
  getTrend: (params) => api.post('/query/statistics/trend', params),
  
  getPeakDemand: (params) => api.post('/query/statistics/peak-demand', params),
  
  getIntensity: (params) => api.post('/query/statistics/intensity', params),
  
  getComparison: (params) => api.post('/query/statistics/comparison', params),
  
  getWeatherCorrelation: (params) => api.post('/query/statistics/weather-correlation', params),
  
  getOccupancyImpact: (params) => api.post('/query/statistics/occupancy-impact', params),
  
  getHourlyPattern: (params) => api.post('/query/statistics/hourly-pattern', params),
  
  getWeeklyPattern: (params) => api.post('/query/statistics/weekly-pattern', params),
  
  getSeasonal: (params) => api.post('/query/statistics/seasonal', params),
  
  getSeasonalPattern: (params) => api.post('/query/statistics/seasonal-pattern', params),

  getAgentReport: (params) => api.post('/query/statistics/agent-report', params, { timeout: 120000 }),
  
  exportReport: (params) => api.post('/query/export/report', params, { responseType: 'blob' })
}

export const visualizationAPI = {
  createLineChart: (data) => api.post('/query/visualization/line-chart', data),
  
  createMultiLineChart: (data) => api.post('/query/visualization/multi-line-chart', data),
  
  createBarChart: (data) => api.post('/query/visualization/bar-chart', data),
  
  createPieChart: (data) => api.post('/query/visualization/pie-chart', data),
  
  createHeatmap: (data) => api.post('/query/visualization/heatmap', data),
  
  createScatterPlot: (data) => api.post('/query/visualization/scatter-plot', data),
  
  createBoxPlot: (data) => api.post('/query/visualization/box-plot', data),
  
  createGaugeChart: (data) => api.post('/query/visualization/gauge-chart', data),
  
  createRadarChart: (data) => api.post('/query/visualization/radar-chart', data),
  
  createAreaChart: (data) => api.post('/query/visualization/area-chart', data),
  
  createHistogram: (data) => api.post('/query/visualization/histogram', data),
  
  createTreemap: (data) => api.post('/query/visualization/treemap', data)
}

export const intelligenceAPI = {
  initializeKnowledgeBase: () => api.post('/intelligence/initialize-knowledge-base'),
  
  addDocument: (formData) => api.post('/intelligence/add-document', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  
  addText: (params) => api.post('/intelligence/add-text', null, { params }),
  
  search: (data) => api.post('/intelligence/search', data),
  
  query: (data) => api.post('/intelligence/query', data),
  
  analyzeAnomaly: (data) => api.post('/intelligence/analyze-anomaly', data),
  
  getEquipmentStatus: (data) => api.post('/intelligence/equipment-status', data),
  
  getEnergySavingSuggestions: (data) => api.post('/intelligence/energy-saving-suggestions', data),
  
  getDataDictionary: () => api.get('/intelligence/data-dictionary'),
  
  getEquipmentManuals: () => api.get('/intelligence/equipment-manuals'),
  
  healthCheck: () => api.get('/intelligence/health')
}

export const mcpAPI = {
  listTools: () => api.get('/mcp/tools'),
  
  callTool: (data) => api.post('/mcp/call-tool', data)
}

export default api
