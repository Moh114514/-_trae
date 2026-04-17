<template>
  <div class="weather-correlation-chart-page">
    <div class="card-header">
      <h2>天气相关性分析</h2>
    </div>
    
    <div class="chart-controls">
      <el-form :model="form" inline>
        <el-form-item label="建筑ID">
          <el-select v-model="form.building_id" placeholder="选择建筑ID" style="width: 150px;">
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
        
        <el-form-item label="温度范围">
          <el-select v-model="form.temperature_range" placeholder="选择温度范围" style="width: 150px;">
            <el-option label="低温 (-10°C 以下)" value="low" />
            <el-option label="中温 (-10°C 到 10°C)" value="medium" />
            <el-option label="高温 (10°C 以上)" value="high" />
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
        <div class="card-title">温度与电力相关性</div>
        <div class="card-value">{{ tempElectricityCorrelation }}</div>
        <div class="card-unit">相关系数</div>
      </div>
      <div class="overview-card">
        <div class="card-title">温度与HVAC相关性</div>
        <div class="card-value">{{ tempHVACCorrelation }}</div>
        <div class="card-unit">相关系数</div>
      </div>
      <div class="overview-card">
        <div class="card-title">湿度与能耗相关性</div>
        <div class="card-value">{{ humidityEnergyCorrelation }}</div>
        <div class="card-unit">相关系数</div>
      </div>
      <div class="overview-card">
        <div class="card-title">平均室外温度</div>
        <div class="card-value">{{ avgTemperature }}</div>
        <div class="card-unit">°C</div>
      </div>
    </div>
    
    <!-- 图表容器 -->
    <div class="charts-grid">
      <!-- 温度与电力消耗相关性 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>温度与电力消耗相关性</h3>
        </div>
        <div ref="tempElectricityChart" class="chart"></div>
      </div>
      
      <!-- 温度与HVAC能耗相关性 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>温度与HVAC能耗相关性</h3>
        </div>
        <div ref="tempHVACChart" class="chart"></div>
      </div>
      
      <!-- 温度分布与能耗关系 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>温度分布与能耗关系</h3>
        </div>
        <div ref="tempDistributionChart" class="chart"></div>
      </div>
      
      <!-- 季节性能耗对比 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>季节性能耗对比</h3>
        </div>
        <div ref="seasonalEnergyChart" class="chart"></div>
      </div>
      
      <!-- 湿度与能耗关系 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>湿度与能耗关系</h3>
        </div>
        <div ref="humidityEnergyChart" class="chart"></div>
      </div>
      
      <!-- 天气因素综合分析 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>天气因素综合分析</h3>
        </div>
        <div ref="weatherFactorsChart" class="chart"></div>
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

const tempElectricityChart = ref(null)
const tempHVACChart = ref(null)
const tempDistributionChart = ref(null)
const seasonalEnergyChart = ref(null)
const humidityEnergyChart = ref(null)
const weatherFactorsChart = ref(null)
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
  temperature_range: 'all'
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
      temperature_range: form.value.temperature_range
    }
    
    try {
      const weatherCorrelationRes = await queryAPI.getWeatherCorrelation(params)
      if (weatherCorrelationRes.data?.error) {
        ElMessage.error(`分析失败: ${weatherCorrelationRes.data.error}`)
        return
      }
      analysisResult.value = weatherCorrelationRes.data
      ElMessage.success('分析完成')
    } catch (apiError) {
      console.error('API调用失败:', apiError)
      ElMessage.error('分析失败，未获取到真实数据')
      return
    }
    
    // 等待DOM更新后渲染图表
    nextTick(() => {
      renderTempElectricityChart()
      renderTempHVACChart()
      renderTempDistributionChart()
      renderSeasonalEnergyChart()
      renderHumidityEnergyChart()
      renderWeatherFactorsChart()
    })
  } catch (error) {
    console.error('分析失败:', error)
    // 错误已在接口分支提示，这里保留上次有效结果
  } finally {
    loading.value = false
  }
}

const safeSetOption = (chartInstance, option, chartName) => {
  try {
    chartInstance.setOption(option)
  } catch (error) {
    console.error(`${chartName}渲染失败:`, error)
    ElMessage.error(`${chartName}渲染失败，请刷新后重试`)
  }
}

const getCorrelations = () => analysisResult.value.correlations || {}

const toFixedOrDash = (value, digits = 2) => {
  const n = Number(value)
  return Number.isFinite(n) ? n.toFixed(digits) : '--'
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

const buildSingleCorrelationOption = (title, label, value, color) => ({
  tooltip: {
    trigger: 'axis',
    formatter: params => {
      if (!params?.length) return ''
      return `${params[0].name}<br/>相关系数: ${Number(params[0].value).toFixed(3)}`
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '15%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: [label]
  },
  yAxis: {
    type: 'value',
    min: -1,
    max: 1,
    name: '相关系数'
  },
  series: [{
    name: title,
    type: 'bar',
    data: [Number(value)],
    itemStyle: { color }
  }]
})

// 计算属性 - 数据概览
const tempElectricityCorrelation = computed(() => toFixedOrDash(getCorrelations().electricity_vs_temp))

const tempHVACCorrelation = computed(() => toFixedOrDash(getCorrelations().hvac_vs_temp))

const humidityEnergyCorrelation = computed(() => toFixedOrDash(getCorrelations().electricity_vs_humidity))

const avgTemperature = computed(() => '--')

// 图表渲染函数
const renderTempElectricityChart = () => {
  if (!tempElectricityChart.value) return
  if (charts.value.tempElectricity) charts.value.tempElectricity.dispose()
  charts.value.tempElectricity = echarts.init(tempElectricityChart.value)

  const value = getCorrelations().electricity_vs_temp
  if (!Number.isFinite(Number(value))) {
    safeSetOption(charts.value.tempElectricity, noDataOption('温度与电力相关性'), '温度电力相关图')
    return
  }
  safeSetOption(
    charts.value.tempElectricity,
    buildSingleCorrelationOption('温度与电力相关性', '温度-电力', value, '#ff6347'),
    '温度电力相关图'
  )
}

const renderTempHVACChart = () => {
  if (!tempHVACChart.value) return
  if (charts.value.tempHVAC) charts.value.tempHVAC.dispose()
  charts.value.tempHVAC = echarts.init(tempHVACChart.value)

  const value = getCorrelations().hvac_vs_temp
  if (!Number.isFinite(Number(value))) {
    safeSetOption(charts.value.tempHVAC, noDataOption('温度与HVAC相关性'), '温度HVAC相关图')
    return
  }
  safeSetOption(
    charts.value.tempHVAC,
    buildSingleCorrelationOption('温度与HVAC相关性', '温度-HVAC', value, '#4682b4'),
    '温度HVAC相关图'
  )
}

const renderTempDistributionChart = () => {
  if (!tempDistributionChart.value) return
  if (charts.value.tempDistribution) charts.value.tempDistribution.dispose()
  charts.value.tempDistribution = echarts.init(tempDistributionChart.value)

  const corr = getCorrelations()
  const values = [
    Number(corr.electricity_vs_temp),
    Number(corr.hvac_vs_temp),
    Number(corr.electricity_vs_humidity)
  ]
  if (!values.some(v => Number.isFinite(v))) {
    safeSetOption(charts.value.tempDistribution, noDataOption('相关性分布'), '相关性分布图')
    return
  }

  const option = {
    tooltip: { trigger: 'axis' },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['温度-电力', '温度-HVAC', '湿度-电力']
    },
    yAxis: {
      type: 'value',
      min: -1,
      max: 1,
      name: '相关系数'
    },
    series: [{
      name: '相关系数',
      type: 'bar',
      data: values.map(v => (Number.isFinite(v) ? v : 0)),
      itemStyle: { color: '#188df0' }
    }]
  }

  safeSetOption(charts.value.tempDistribution, option, '相关性分布图')
}

const renderSeasonalEnergyChart = () => {
  if (!seasonalEnergyChart.value) return
  if (charts.value.seasonalEnergy) charts.value.seasonalEnergy.dispose()
  charts.value.seasonalEnergy = echarts.init(seasonalEnergyChart.value)
  safeSetOption(charts.value.seasonalEnergy, noDataOption('季节性能耗对比'), '季节性能耗图')
}

const renderHumidityEnergyChart = () => {
  if (!humidityEnergyChart.value) return
  if (charts.value.humidityEnergy) charts.value.humidityEnergy.dispose()
  charts.value.humidityEnergy = echarts.init(humidityEnergyChart.value)

  const value = getCorrelations().electricity_vs_humidity
  if (!Number.isFinite(Number(value))) {
    safeSetOption(charts.value.humidityEnergy, noDataOption('湿度与能耗相关性'), '湿度能耗相关图')
    return
  }
  safeSetOption(
    charts.value.humidityEnergy,
    buildSingleCorrelationOption('湿度与电力相关性', '湿度-电力', value, '#32cd32'),
    '湿度能耗相关图'
  )
}

const renderWeatherFactorsChart = () => {
  if (!weatherFactorsChart.value) return
  if (charts.value.weatherFactors) charts.value.weatherFactors.dispose()
  charts.value.weatherFactors = echarts.init(weatherFactorsChart.value)

  const corr = getCorrelations()
  const categories = ['温度-电力', '温度-HVAC', '湿度-电力', '湿度-HVAC']
  const values = [
    Number(corr.electricity_vs_temp),
    Number(corr.hvac_vs_temp),
    Number(corr.electricity_vs_humidity),
    Number(corr.hvac_vs_humidity)
  ]
  if (!values.some(v => Number.isFinite(v))) {
    safeSetOption(charts.value.weatherFactors, noDataOption('天气因素综合分析'), '天气因素综合图')
    return
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: categories
    },
    yAxis: {
      type: 'value',
      min: -1,
      max: 1,
      name: '相关系数'
    },
    series: [{
      name: '相关系数',
      type: 'bar',
      data: values.map(v => (Number.isFinite(v) ? v : 0)),
      itemStyle: {
        color: params => (Number(params.value) >= 0 ? '#52c41a' : '#ff4d4f')
      }
    }]
  }

  safeSetOption(charts.value.weatherFactors, option, '天气因素综合图')
}

// 数据导出
const exportData = (format) => {
  const corr = getCorrelations()
  const exportData = [
    { factor: '温度-电力', value: Number(corr.electricity_vs_temp) },
    { factor: '温度-HVAC', value: Number(corr.hvac_vs_temp) },
    { factor: '湿度-电力', value: Number(corr.electricity_vs_humidity) },
    { factor: '湿度-HVAC', value: Number(corr.hvac_vs_humidity) }
  ].filter(item => Number.isFinite(item.value))

  if (exportData.length === 0) {
    ElMessage.warning('当前无可导出的真实数据')
    return
  }

  let csvContent = '天气因素,相关系数\n'
  exportData.forEach(item => {
    csvContent += `${item.factor},${item.value.toFixed(4)}\n`
  })
  
  // 创建下载链接
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `天气相关性分析_${new Date().toISOString().split('T')[0]}.${format}`)
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
.weather-correlation-chart-page {
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