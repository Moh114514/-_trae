import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as echarts from 'echarts'

import App from './App.vue'
import router from './router'
import { setupIconFix } from './utils/iconFix'

const CARTESIAN_SERIES_TYPES = new Set([
  'line',
  'bar',
  'scatter',
  'effectScatter',
  'candlestick',
  'boxplot',
  'heatmap'
])

const normalizeCartesianAxes = (option, seriesList) => {
  const hasCartesianSeries = seriesList.some(s => CARTESIAN_SERIES_TYPES.has(s.type))
  if (!hasCartesianSeries) {
    return
  }

  if (option.xAxis == null) {
    option.xAxis = { type: 'category', data: [] }
  } else if (Array.isArray(option.xAxis) && option.xAxis.length === 0) {
    option.xAxis = [{ type: 'category', data: [] }]
  }

  if (option.yAxis == null) {
    option.yAxis = { type: 'value' }
  } else if (Array.isArray(option.yAxis) && option.yAxis.length === 0) {
    option.yAxis = [{ type: 'value' }]
  }
}

const patchEchartsSetOption = () => {
  if (!echarts || typeof echarts.init !== 'function') {
    return
  }
  if (typeof window === 'undefined' || typeof document === 'undefined' || !document.body) {
    return
  }

  if (window.__beimsEchartsPatched) {
    return
  }

  const probeEl = document.createElement('div')
  probeEl.style.width = '1px'
  probeEl.style.height = '1px'
  probeEl.style.position = 'fixed'
  probeEl.style.left = '-9999px'
  probeEl.style.top = '-9999px'
  document.body.appendChild(probeEl)

  const probeChart = echarts.init(probeEl)
  const proto = Object.getPrototypeOf(probeChart)

  if (proto && !proto.__beimsSafePatched) {
    const originalSetOption = proto.setOption
    proto.setOption = function patchedSetOption(option, ...rest) {
      if (!option || typeof option !== 'object') {
        return originalSetOption.call(this, option, ...rest)
      }

      const safeOption = { ...option }

      if ('series' in safeOption) {
        const rawSeries = Array.isArray(safeOption.series)
          ? safeOption.series
          : [safeOption.series]
        const validSeries = rawSeries.filter(
          item => item && typeof item === 'object' && typeof item.type === 'string'
        )
        safeOption.series = validSeries
        normalizeCartesianAxes(safeOption, validSeries)
      }

      return originalSetOption.call(this, safeOption, ...rest)
    }

    proto.__beimsSafePatched = true
  }

  probeChart.dispose()
  probeEl.remove()
  window.__beimsEchartsPatched = true
}

patchEchartsSetOption()

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })

app.mount('#app')

// 应用图标修复
setupIconFix()
