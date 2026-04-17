<template>
  <div class="comparison-chart-page">
    <div class="card-header">
      <h2>对比分析</h2>
    </div>
    
    <div class="chart-controls">
      <el-form :model="form" inline>
        <el-form-item label="建筑ID">
          <el-select v-model="form.building_ids" multiple placeholder="选择建筑ID" style="width: 300px;">
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
        <div class="card-title">平均电力消耗</div>
        <div class="card-value">{{ avgElectricity }}</div>
        <div class="card-unit">kWh</div>
      </div>
      <div class="overview-card">
        <div class="card-title">平均HVAC能耗</div>
        <div class="card-value">{{ avgHVAC }}</div>
        <div class="card-unit">kWh</div>
      </div>
      <div class="overview-card">
        <div class="card-title">平均用水量</div>
        <div class="card-value">{{ avgWater }}</div>
        <div class="card-unit">m³</div>
      </div>
      <div class="overview-card">
        <div class="card-title">总能耗</div>
        <div class="card-value">{{ totalEnergy }}</div>
        <div class="card-unit">kWh</div>
      </div>
    </div>
    
    <!-- 图表容器 -->
    <div class="charts-grid">
      <!-- 能耗对比图 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>能耗对比</h3>
        </div>
        <div ref="comparisonChart" class="chart"></div>
      </div>
      
      <!-- 能耗强度对比图 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>能耗强度对比</h3>
        </div>
        <div ref="intensityChart" class="chart"></div>
      </div>
      
      <!-- 能耗趋势对比图 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>能耗趋势对比</h3>
        </div>
        <div ref="trendChart" class="chart"></div>
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

const comparisonChart = ref(null)
const intensityChart = ref(null)
const trendChart = ref(null)
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
  building_ids: [],
  start_time: startDate.toISOString().slice(0, 19).replace('T', ' '),
  end_time: endDate.toISOString().slice(0, 19).replace('T', ' ')
})

const loadBuildings = async () => {
  try {
    const res = await dataAPI.getBuildings()
    buildings.value = res.data.buildings
    
    // 如果有建筑数据，自动选择前几个建筑作为默认值
    if (buildings.value.length > 0) {
      form.value.building_ids = buildings.value.slice(0, 3).map(b => b.building_id)
    } else {
      // 如果没有建筑数据，设置一些默认的建筑ID
      form.value.building_ids = ['Aral', 'Baikal', 'Caspian']
    }
  } catch (error) {
    console.error('加载建筑列表失败:', error)
    // 如果加载失败，设置一些默认的建筑ID
    form.value.building_ids = ['Aral', 'Baikal', 'Caspian']
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
    if (!form.value.building_ids || form.value.building_ids.length === 0) {
      ElMessage.warning('请选择至少一个建筑ID')
      loading.value = false
      return
    }
    
    if (!form.value.start_time || !form.value.end_time) {
      ElMessage.warning('请选择开始时间和结束时间')
      loading.value = false
      return
    }
    
    const params = {
      building_ids: form.value.building_ids,
      start_time: form.value.start_time,
      end_time: form.value.end_time
    }
    
    try {
      const comparisonRes = await queryAPI.getComparison(params)
      if (comparisonRes.data?.error) {
        ElMessage.error(`分析失败: ${comparisonRes.data.error}`)
        return
      }
      analysisResult.value = comparisonRes.data
      ElMessage.success('分析完成')
    } catch (apiError) {
      console.error('API调用失败:', apiError)
      ElMessage.error('分析失败，未获取到真实数据')
      return
    }
    
    // 等待DOM更新后渲染图表
    nextTick(() => {
      renderComparisonChart()
      renderIntensityChart()
      renderTrendChart()
    })
  } catch (error) {
    console.error('分析失败:', error)
    // 错误已在接口分支提示，这里保留上次有效结果
  } finally {
    loading.value = false
  }
}

const getComparisonData = () => analysisResult.value.comparison_data || {}

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
const avgElectricity = computed(() => {
  const comparisonData = getComparisonData()
  const buildings = Object.keys(comparisonData)
  if (buildings.length > 0) {
    const sum = buildings.reduce((acc, building) => acc + comparisonData[building].total_electricity, 0)
    return (sum / buildings.length).toFixed(0)
  }
  return '--'
})

const avgHVAC = computed(() => {
  const comparisonData = getComparisonData()
  const buildings = Object.keys(comparisonData)
  if (buildings.length > 0) {
    const sum = buildings.reduce((acc, building) => acc + comparisonData[building].total_hvac, 0)
    return (sum / buildings.length).toFixed(0)
  }
  return '--'
})

const avgWater = computed(() => {
  const comparisonData = getComparisonData()
  const buildings = Object.keys(comparisonData)
  if (buildings.length > 0) {
    const sum = buildings.reduce((acc, building) => acc + comparisonData[building].total_water, 0)
    return (sum / buildings.length).toFixed(0)
  }
  return '--'
})

const totalEnergy = computed(() => {
  const comparisonData = getComparisonData()
  const buildings = Object.keys(comparisonData)
  if (buildings.length > 0) {
    const sum = buildings.reduce((acc, building) => acc + comparisonData[building].total_electricity + comparisonData[building].total_hvac, 0)
    return Math.round(sum)
  }
  return '--'
})

const renderComparisonChart = () => {
  if (!comparisonChart.value) return
  
  if (charts.value.comparison) {
    charts.value.comparison.dispose()
  }
  
  charts.value.comparison = echarts.init(comparisonChart.value)
  
  const comparisonData = getComparisonData()
  const xAxisData = Object.keys(comparisonData)
  if (xAxisData.length === 0) {
    safeSetOption(charts.value.comparison, noDataOption('能耗对比'), '能耗对比图')
    return
  }

  const electricityData = xAxisData.map(building => comparisonData[building].total_electricity)
  const hvacData = xAxisData.map(building => comparisonData[building].total_hvac)
  const waterData = xAxisData.map(building => comparisonData[building].total_water)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['电力消耗(kWh)', 'HVAC能耗(kWh)', '用水量(m³)'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '能耗'
    },
    series: [
      {
        name: '电力消耗(kWh)',
        type: 'bar',
        data: electricityData,
        itemStyle: {
          color: '#4169e1'
        }
      },
      {
        name: 'HVAC能耗(kWh)',
        type: 'bar',
        data: hvacData,
        itemStyle: {
          color: '#ff7f50'
        }
      },
      {
        name: '用水量(m³)',
        type: 'bar',
        data: waterData,
        itemStyle: {
          color: '#87ceeb'
        }
      }
    ]
  }
  
  safeSetOption(charts.value.comparison, option, '能耗对比图')
}

const renderIntensityChart = () => {
  if (!intensityChart.value) return
  
  if (charts.value.intensity) {
    charts.value.intensity.dispose()
  }
  
  charts.value.intensity = echarts.init(intensityChart.value)
  
  const comparisonData = getComparisonData()
  const xAxisData = Object.keys(comparisonData)
  if (xAxisData.length === 0) {
    safeSetOption(charts.value.intensity, noDataOption('能耗强度对比'), '能耗强度对比图')
    return
  }

  const intensityData = xAxisData.map(building => {
    const total = Number(comparisonData[building].total_electricity || 0) + Number(comparisonData[building].total_hvac || 0)
    return total / 1000
  })
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: function(params) {
        return `${params[0].name}<br/>${params[0].seriesName}: ${params[0].value.toFixed(2)} kWh/m²`
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
      data: xAxisData,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '能耗强度(kWh/m²)'
    },
    series: [
      {
        name: '能耗强度',
        type: 'bar',
        data: intensityData,
        itemStyle: {
          color: '#9370db'
        },
        markPoint: {
          data: [
            { type: 'max', name: '最大值' },
            { type: 'min', name: '最小值' }
          ]
        },
        markLine: {
          data: [
            { type: 'average', name: '平均值' }
          ]
        }
      }
    ]
  }
  
  safeSetOption(charts.value.intensity, option, '能耗强度对比图')
}

const renderTrendChart = () => {
  if (!trendChart.value) return
  
  if (charts.value.trend) {
    charts.value.trend.dispose()
  }
  
  charts.value.trend = echarts.init(trendChart.value)
  const comparisonData = getComparisonData()
  const xAxisData = Object.keys(comparisonData)
  if (xAxisData.length === 0) {
    safeSetOption(charts.value.trend, noDataOption('能耗趋势对比'), '能耗趋势对比图')
    return
  }

  const totalSeries = xAxisData.map(building => Number(comparisonData[building].total_electricity || 0) + Number(comparisonData[building].total_hvac || 0))
  const avgSeries = xAxisData.map(building => Number(comparisonData[building].avg_electricity || 0) + Number(comparisonData[building].avg_hvac || 0))
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['总能耗', '平均能耗'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xAxisData
    },
    yAxis: {
      type: 'value',
      name: '总能耗(kWh)'
    },
    series: [
      {
        name: '总能耗',
        type: 'line',
        data: totalSeries,
        smooth: true,
        itemStyle: {
          color: '#4169e1'
        }
      },
      {
        name: '平均能耗',
        type: 'line',
        data: avgSeries,
        smooth: true,
        itemStyle: {
          color: '#ff7f50'
        }
      }
    ]
  }
  
  safeSetOption(charts.value.trend, option, '能耗趋势对比图')
}

// 数据导出
const exportData = (format) => {
  const comparisonData = getComparisonData()
  if (Object.keys(comparisonData).length === 0) {
    ElMessage.warning('当前无可导出的真实数据')
    return
  }

  const exportData = []
  for (const [building, data] of Object.entries(comparisonData)) {
    exportData.push({
      building: building,
      electricity: data.total_electricity,
      hvac: data.total_hvac,
      water: data.total_water,
      total: data.total_electricity + data.total_hvac
    })
  }
  
  // 生成CSV内容
  let csvContent = '建筑,电力消耗(kWh),HVAC能耗(kWh),用水量(m³),总能耗(kWh)\n'
  exportData.forEach(item => {
    csvContent += `${item.building},${item.electricity.toFixed(2)},${item.hvac.toFixed(2)},${item.water.toFixed(2)},${item.total.toFixed(2)}\n`
  })
  
  // 创建下载链接
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `对比分析_${new Date().toISOString().split('T')[0]}.${format}`)
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
.comparison-chart-page {
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
  margin-top: 0px;
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