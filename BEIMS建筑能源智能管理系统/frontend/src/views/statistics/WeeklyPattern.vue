<template>
  <div class="weekly-pattern-chart-page">
    <div class="card-header">
      <h2>周模式分析</h2>
    </div>
    
    <div class="chart-controls">
      <el-form :model="form" inline>
        <el-form-item label="建筑ID">
          <el-select v-model="form.building_id" placeholder="选择建筑ID" style="width: 150px;" @change="handleAnalyze">
            <el-option
              v-for="building in buildings"
              :key="building.building_id"
              :label="building.building_id"
              :value="building.building_id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="form.start_time"
            type="datetime"
            placeholder="选择开始时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="form.end_time"
            type="datetime"
            placeholder="选择结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        
        <el-form-item label="季节">
          <el-select v-model="form.season" placeholder="选择季节" style="width: 150px;">
            <el-option label="春季 (3-5月)" value="spring" />
            <el-option label="夏季 (6-8月)" value="summer" />
            <el-option label="秋季 (9-11月)" value="autumn" />
            <el-option label="冬季 (12-2月)" value="winter" />
            <el-option label="全部" value="all" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleAnalyze">开始分析</el-button>
        </el-form-item>
      </el-form>
      
      <!-- 时间范围快速选择 -->
      <div class="time-range-buttons">
        <el-button size="large" @click="setTimeRange('today')" :type="selectedRange === 'today' ? 'primary' : 'default'">今天</el-button>
        <el-button size="large" @click="setTimeRange('week')" :type="selectedRange === 'week' ? 'primary' : 'default'">本周</el-button>
        <el-button size="large" @click="setTimeRange('month')" :type="selectedRange === 'month' ? 'primary' : 'default'">本月</el-button>
        <el-button size="large" @click="setTimeRange('year')" :type="selectedRange === 'year' ? 'primary' : 'default'">本年</el-button>
      </div>
    </div>
    
    <!-- 数据概览卡片 -->
    <div class="overview-cards">
      <div class="overview-card">
        <div class="card-title">工作日平均能耗</div>
        <div class="card-value">{{ weekdayAvgEnergy }}</div>
        <div class="card-unit">kWh</div>
      </div>
      <div class="overview-card">
        <div class="card-title">周末平均能耗</div>
        <div class="card-value">{{ weekendAvgEnergy }}</div>
        <div class="card-unit">kWh</div>
      </div>
      <div class="overview-card">
        <div class="card-title">周平均能耗</div>
        <div class="card-value">{{ weeklyAvgEnergy }}</div>
        <div class="card-unit">kWh</div>
      </div>
      <div class="overview-card">
        <div class="card-title">总能耗</div>
        <div class="card-value">{{ totalEnergy }}</div>
        <div class="card-unit">kWh</div>
      </div>
    </div>
    
    <!-- 图表容器 -->
    <div class="charts-grid">
      <!-- 周能耗趋势 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>周能耗趋势</h3>
        </div>
        <div ref="weeklyTrendChart" class="chart"></div>
      </div>
      
      <!-- 工作日vs周末对比 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>工作日vs周末对比</h3>
        </div>
        <div ref="weekdayWeekendChart" class="chart"></div>
      </div>
      
      <!-- 能耗构成分析 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>能耗构成分析</h3>
        </div>
        <div ref="energyCompositionChart" class="chart"></div>
      </div>
      
      <!-- 周能耗分布 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>周能耗分布</h3>
        </div>
        <div ref="energyDistributionChart" class="chart"></div>
      </div>
      
      <!-- 能耗变化率分析 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>能耗变化率分析</h3>
        </div>
        <div ref="energyChangeRateChart" class="chart"></div>
      </div>
      
      <!-- 周能耗与时间关系 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>周能耗与时间关系</h3>
        </div>
        <div ref="energyTimeRelationChart" class="chart"></div>
      </div>
    </div>
    
    <!-- 数据导出 -->
    <div class="export-section">
      <el-button type="success" @click="exportData('csv')">导出CSV</el-button>
      <el-button type="success" @click="exportData('excel')">导出Excel</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { dataAPI, queryAPI } from '@/api'

const weeklyTrendChart = ref(null)
const weekdayWeekendChart = ref(null)
const energyCompositionChart = ref(null)
const energyDistributionChart = ref(null)
const energyChangeRateChart = ref(null)
const energyTimeRelationChart = ref(null)
const charts = ref({})
const buildings = ref([])
const loading = ref(false)
const analysisResult = ref({})
const selectedRange = ref('week')
const selectedDays = ref(7)

// 设置默认时间范围为包含数据库中数据的时间范围
const startDate = new Date('2021-01-01')
const endDate = new Date('2021-01-31')

const form = ref({
  building_id: '',
  start_time: startDate.toISOString().slice(0, 19).replace('T', ' '),
  end_time: endDate.toISOString().slice(0, 19).replace('T', ' '),
  season: 'all'
})

const loadBuildings = async () => {
  try {
    const res = await dataAPI.getBuildings()
    buildings.value = res.data.buildings
    
    // 如果有建筑数据，自动选择第一个建筑作为默认值
    if (buildings.value.length > 0) {
      form.value.building_id = buildings.value[0].building_id
    } else {
      // 如果没有建筑数据，设置一个默认的建筑ID
      form.value.building_id = 'Aral'
    }
  } catch (error) {
    console.error('加载建筑列表失败:', error)
    // 如果加载失败，设置一个默认的建筑ID
    form.value.building_id = 'Aral'
  }
}

// 时间范围快速选择
const setTimeRange = (range) => {
  // 获取当前系统时间，确保与综合概览时间同步
  const currentDate = new Date()
  // 使用2021年作为默认年份，以适应数据集
  const now = new Date(currentDate.getFullYear() === 2026 ? '2021' + currentDate.toISOString().slice(4) : currentDate)
  let start, end, days
  
  selectedRange.value = range
  
  switch (range) {
    case 'today':
      start = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      end = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59)
      days = 1
      break
    case 'week':
      start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - now.getDay())
      end = new Date(now.getFullYear(), now.getMonth(), now.getDate() - now.getDay() + 6, 23, 59, 59)
      days = 7
      break
    case 'month':
      start = new Date(now.getFullYear(), now.getMonth(), 1)
      end = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59)
      days = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate()
      break
    case 'year':
      start = new Date(now.getFullYear(), 0, 1)
      end = new Date(now.getFullYear(), 11, 31, 23, 59, 59)
      days = 365
      break
  }
  
  form.value.start_time = start.toISOString().slice(0, 19).replace('T', ' ')
  form.value.end_time = end.toISOString().slice(0, 19).replace('T', ' ')
  // 存储当前选择的天数，用于生成默认数据
  selectedDays.value = days
  handleAnalyze()
}

const handleAnalyze = async () => {
  loading.value = true
  
  try {
    // 验证必要参数
    if (!form.value.building_id) {
      ElMessage.warning('请选择建筑ID')
      loading.value = false
      return
    }
    
    if (!form.value.start_time || !form.value.end_time) {
      ElMessage.warning('请选择开始时间和结束时间')
      loading.value = false
      return
    }
    
    const params = {
      building_id: form.value.building_id,
      start_time: form.value.start_time,
      end_time: form.value.end_time,
      season: form.value.season
    }
    
    try {
      const weeklyPatternRes = await queryAPI.getWeeklyPattern(params)
      if (weeklyPatternRes.data?.error) {
        ElMessage.error(`分析失败: ${weeklyPatternRes.data.error}`)
        return
      }
      analysisResult.value = weeklyPatternRes.data
      ElMessage.success('分析完成')
    } catch (apiError) {
      console.error('API调用失败:', apiError)
      ElMessage.error('分析失败，未获取到真实数据')
      return
    }
    
    // 等待DOM更新后渲染图表
    nextTick(() => {
      renderWeeklyTrendChart()
      renderWeekdayWeekendChart()
      renderEnergyCompositionChart()
      renderEnergyDistributionChart()
      renderEnergyChangeRateChart()
      renderEnergyTimeRelationChart()
    })
  } catch (error) {
    console.error('分析失败:', error)
    // 错误已在接口分支提示，这里保留上次有效结果
  } finally {
    loading.value = false
  }
}

const DAY_ORDER = [
  { en: 'Monday', zh: '周一' },
  { en: 'Tuesday', zh: '周二' },
  { en: 'Wednesday', zh: '周三' },
  { en: 'Thursday', zh: '周四' },
  { en: 'Friday', zh: '周五' },
  { en: 'Saturday', zh: '周六' },
  { en: 'Sunday', zh: '周日' }
]

const getWeeklySeries = () => {
  const weeklyPattern = analysisResult.value.weekly_pattern || {}
  return DAY_ORDER.map((day, index) => {
    const item = weeklyPattern[day.en] || {}
    const electricity = Number(item.electricity_kwh || 0)
    const hvac = Number(item.hvac_kwh || 0)
    const water = Number(item.water_m3 || 0)
    return {
      ...day,
      index,
      electricity,
      hvac,
      water,
      total: electricity + hvac
    }
  })
}

const getValidWeeklySeries = () => getWeeklySeries().filter(item => item.total > 0 || item.water > 0)

const safeSetOption = (chartInstance, option, chartName) => {
  try {
    chartInstance.setOption(option)
  } catch (error) {
    console.error(`${chartName}渲染失败:`, error)
    ElMessage.error(`${chartName}渲染失败，请刷新后重试`)
  }
}

const noDataOption = (title) => ({
  title: {
    text: `${title}（暂无数据）`,
    left: 'center'
  },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value' },
  series: [{ type: 'bar', data: [] }]
})

// 计算属性 - 数据概览
const weekdayAvgEnergy = computed(() => {
  const weekdayData = getValidWeeklySeries().filter(item => item.index < 5)
  if (weekdayData.length === 0) return '--'
  const avg = weekdayData.reduce((sum, item) => sum + item.total, 0) / weekdayData.length
  return avg.toFixed(2)
})

const weekendAvgEnergy = computed(() => {
  const weekendData = getValidWeeklySeries().filter(item => item.index >= 5)
  if (weekendData.length === 0) return '--'
  const avg = weekendData.reduce((sum, item) => sum + item.total, 0) / weekendData.length
  return avg.toFixed(2)
})

const weeklyAvgEnergy = computed(() => {
  const series = getValidWeeklySeries()
  if (series.length === 0) return '--'
  const avg = series.reduce((sum, item) => sum + item.total, 0) / series.length
  return avg.toFixed(2)
})

const totalEnergy = computed(() => {
  const series = getValidWeeklySeries()
  if (series.length === 0) return '--'
  return Math.round(series.reduce((sum, item) => sum + item.total, 0))
})

// 图表渲染函数
const renderWeeklyTrendChart = () => {
  if (!weeklyTrendChart.value) return
  if (charts.value.weeklyTrend) charts.value.weeklyTrend.dispose()
  charts.value.weeklyTrend = echarts.init(weeklyTrendChart.value)

  const series = getWeeklySeries()
  const hasData = series.some(item => item.total > 0)
  if (!hasData) {
    safeSetOption(charts.value.weeklyTrend, noDataOption('周能耗趋势'), '周能耗趋势图')
    return
  }

  const option = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: { data: ['电力消耗', 'HVAC能耗', '总能耗'], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: { type: 'category', data: series.map(item => item.zh) },
    yAxis: { type: 'value', name: '能耗(kWh)' },
    series: [
      {
        name: '电力消耗',
        type: 'line',
        stack: 'Total',
        areaStyle: { opacity: 0.3 },
        lineStyle: { width: 3 },
        itemStyle: { color: '#ff7f50' },
        data: series.map(item => item.electricity)
      },
      {
        name: 'HVAC能耗',
        type: 'line',
        stack: 'Total',
        areaStyle: { opacity: 0.3 },
        lineStyle: { width: 3 },
        itemStyle: { color: '#4682b4' },
        data: series.map(item => item.hvac)
      },
      {
        name: '总能耗',
        type: 'line',
        lineStyle: { width: 4, type: 'dashed' },
        itemStyle: { color: '#ff6b6b' },
        data: series.map(item => item.total)
      }
    ]
  }

  safeSetOption(charts.value.weeklyTrend, option, '周能耗趋势图')
}

const renderWeekdayWeekendChart = () => {
  if (!weekdayWeekendChart.value) return
  if (charts.value.weekdayWeekend) charts.value.weekdayWeekend.dispose()
  charts.value.weekdayWeekend = echarts.init(weekdayWeekendChart.value)

  const series = getValidWeeklySeries()
  if (series.length === 0) {
    safeSetOption(charts.value.weekdayWeekend, noDataOption('工作日vs周末对比'), '工作日周末对比图')
    return
  }

  const weekday = series.filter(item => item.index < 5)
  const weekend = series.filter(item => item.index >= 5)
  const avgOf = (arr, key) => (arr.length ? arr.reduce((sum, item) => sum + item[key], 0) / arr.length : 0)
  const weekdayData = [
    avgOf(weekday, 'electricity'),
    avgOf(weekday, 'hvac'),
    avgOf(weekday, 'water'),
    avgOf(weekday, 'total')
  ]
  const weekendData = [
    avgOf(weekend, 'electricity'),
    avgOf(weekend, 'hvac'),
    avgOf(weekend, 'water'),
    avgOf(weekend, 'total')
  ]

  const maxValues = weekdayData.map((value, idx) => Math.max(value, weekendData[idx]) * 1.2 || 1)
  const indicator = [
    { name: '电力消耗', max: maxValues[0] },
    { name: 'HVAC能耗', max: maxValues[1] },
    { name: '用水量', max: maxValues[2] },
    { name: '总能耗', max: maxValues[3] }
  ]

  const option = {
    tooltip: { trigger: 'item' },
    legend: { data: ['工作日', '周末'], bottom: 0 },
    radar: { indicator },
    series: [{
      name: '工作日 vs 周末',
      type: 'radar',
      data: [
        { value: weekdayData, name: '工作日', areaStyle: { opacity: 0.3 }, itemStyle: { color: '#4682b4' } },
        { value: weekendData, name: '周末', areaStyle: { opacity: 0.3 }, itemStyle: { color: '#ff7f50' } }
      ]
    }]
  }

  safeSetOption(charts.value.weekdayWeekend, option, '工作日周末对比图')
}

const renderEnergyCompositionChart = () => {
  if (!energyCompositionChart.value) return
  if (charts.value.energyComposition) charts.value.energyComposition.dispose()
  charts.value.energyComposition = echarts.init(energyCompositionChart.value)

  const series = getValidWeeklySeries()
  if (series.length === 0) {
    safeSetOption(charts.value.energyComposition, noDataOption('能耗构成分析'), '能耗构成图')
    return
  }

  const electricity = series.reduce((sum, item) => sum + item.electricity, 0)
  const hvac = series.reduce((sum, item) => sum + item.hvac, 0)
  const water = series.reduce((sum, item) => sum + item.water, 0)
  const option = {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { data: ['电力', 'HVAC', '用水'], bottom: 0 },
    series: [{
      name: '能耗构成',
      type: 'pie',
      radius: ['40%', '70%'],
      data: [
        { value: electricity, name: '电力' },
        { value: hvac, name: 'HVAC' },
        { value: water, name: '用水' }
      ]
    }]
  }

  safeSetOption(charts.value.energyComposition, option, '能耗构成图')
}

const renderEnergyDistributionChart = () => {
  if (!energyDistributionChart.value) return
  if (charts.value.energyDistribution) charts.value.energyDistribution.dispose()
  charts.value.energyDistribution = echarts.init(energyDistributionChart.value)

  const series = getValidWeeklySeries()
  if (series.length === 0) {
    safeSetOption(charts.value.energyDistribution, noDataOption('周能耗分布'), '周能耗分布图')
    return
  }

  const weekdayData = series.filter(item => item.index < 5).map(item => [item.index, item.total])
  const weekendData = series.filter(item => item.index >= 5).map(item => [item.index, item.total])
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: params => `${DAY_ORDER[params.value[0]].zh}: ${Number(params.value[1]).toFixed(2)} kWh`
    },
    legend: { data: ['工作日', '周末'], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: { type: 'category', data: DAY_ORDER.map(item => item.zh), name: '星期' },
    yAxis: { type: 'value', name: '能耗(kWh)' },
    series: [
      { name: '工作日', type: 'scatter', data: weekdayData, symbolSize: 20, itemStyle: { color: '#4682b4' } },
      { name: '周末', type: 'scatter', data: weekendData, symbolSize: 18, itemStyle: { color: '#ff7f50' } }
    ]
  }

  safeSetOption(charts.value.energyDistribution, option, '周能耗分布图')
}

const renderEnergyChangeRateChart = () => {
  if (!energyChangeRateChart.value) return
  if (charts.value.energyChangeRate) charts.value.energyChangeRate.dispose()
  charts.value.energyChangeRate = echarts.init(energyChangeRateChart.value)

  const series = getWeeklySeries()
  const hasData = series.some(item => item.total > 0)
  if (!hasData) {
    safeSetOption(charts.value.energyChangeRate, noDataOption('能耗变化率分析'), '能耗变化率图')
    return
  }

  const changeRateData = series.map((item, index) => {
    if (index === 0 || series[index - 1].total === 0) return 0
    return Number((((item.total - series[index - 1].total) / series[index - 1].total) * 100).toFixed(1))
  })

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: params => `${params[0].name}<br/>${params[0].seriesName}: ${params[0].value}%`
    },
    legend: { data: ['能耗变化率'], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: { type: 'category', data: DAY_ORDER.map(item => item.zh) },
    yAxis: {
      type: 'value',
      name: '变化率(%)',
      axisLabel: { formatter: '{value}%' }
    },
    series: [{
      name: '能耗变化率',
      type: 'line',
      data: changeRateData,
      itemStyle: {
        color: params => (Number(params.value) >= 0 ? '#52c41a' : '#ff4d4f')
      },
      lineStyle: { width: 3 },
      symbol: 'circle',
      symbolSize: 8
    }]
  }

  safeSetOption(charts.value.energyChangeRate, option, '能耗变化率图')
}

const renderEnergyTimeRelationChart = () => {
  if (!energyTimeRelationChart.value) return
  if (charts.value.energyTimeRelation) charts.value.energyTimeRelation.dispose()
  charts.value.energyTimeRelation = echarts.init(energyTimeRelationChart.value)

  const series = getValidWeeklySeries()
  if (series.length === 0) {
    safeSetOption(charts.value.energyTimeRelation, noDataOption('周能耗与时间关系'), '能耗时间关系图')
    return
  }

  const points = series.map(item => [item.index * 24 + 12, item.total, item.zh])
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: params => `${params[0].value[2]} 12:00<br/>能耗: ${Number(params[0].value[1]).toFixed(2)} kWh`
    },
    legend: { data: ['能耗'], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: { type: 'value', name: '时间(小时)', max: 168 },
    yAxis: { type: 'value', name: '能耗(kWh)' },
    series: [{
      name: '能耗',
      type: 'scatter',
      data: points,
      symbolSize: 10,
      itemStyle: {
        color: params => (params.value[0] < 120 ? '#4682b4' : '#ff7f50')
      }
    }]
  }

  safeSetOption(charts.value.energyTimeRelation, option, '能耗时间关系图')
}

// 数据导出
const exportData = (format) => {
  const exportData = getValidWeeklySeries()
  if (exportData.length === 0) {
    ElMessage.warning('当前无可导出的真实数据')
    return
  }
  
  // 生成CSV内容
  let csvContent = '星期,电力消耗(kWh),HVAC能耗(kWh),总能耗(kWh)\n'
  exportData.forEach(item => {
    csvContent += `${item.zh},${item.electricity.toFixed(2)},${item.hvac.toFixed(2)},${item.total.toFixed(2)}\n`
  })
  
  // 创建下载链接
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `周模式分析_${new Date().toISOString().split('T')[0]}.${format}`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// 监听窗口大小变化，调整图表大小
window.addEventListener('resize', () => {
  Object.values(charts.value).forEach(chart => {
    chart?.resize()
  })
})

onMounted(async () => {
  await loadBuildings()
  setTimeRange('week')
})
</script>

<style scoped>
.weekly-pattern-chart-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  margin-bottom: 20px;
}

.chart-controls {
  background-color: #f5f7fa;
  padding: 20px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.time-range-buttons {
  display: flex;
  gap: 10px;
  margin-top: 10px;
  justify-content: flex-end;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.overview-card {
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  text-align: center;
  transition: transform 0.3s ease;
}

.overview-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.15);
}

.card-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 10px;
}

.card-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.card-unit {
  font-size: 12px;
  color: #909399;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.chart-item {
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.chart-header {
  margin-bottom: 15px;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 10px;
}

.chart-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.chart {
  width: 100%;
  height: 350px;
}

.export-section {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .overview-cards {
    grid-template-columns: 1fr;
  }
  
  .time-range-buttons {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .chart-controls {
    padding: 15px;
  }
  
  .chart {
    height: 300px;
  }
}
</style>