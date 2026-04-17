<template>
  <div class="occupancy-impact-chart-page">
    <div class="card-header">
      <h2>人员影响分析</h2>
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
        
        <el-form-item label="人员密度范围">
          <el-select v-model="form.occupancy_range" placeholder="选择人员密度范围" style="width: 150px;">
            <el-option label="低 (0-30%)" value="low" />
            <el-option label="中 (30-70%)" value="medium" />
            <el-option label="高 (70-100%)" value="high" />
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
        <div class="card-title">人员密度与能耗相关性</div>
        <div class="card-value">{{ occupancyCorrelation }}</div>
        <div class="card-unit">相关系数</div>
      </div>
      <div class="overview-card">
        <div class="card-title">平均人员密度</div>
        <div class="card-value">{{ avgOccupancy }}</div>
        <div class="card-unit">%</div>
      </div>
      <div class="overview-card">
        <div class="card-title">人均能耗</div>
        <div class="card-value">{{ perCapitaEnergy }}</div>
        <div class="card-unit">kWh/人</div>
      </div>
      <div class="overview-card">
        <div class="card-title">总能耗</div>
        <div class="card-value">{{ totalEnergy }}</div>
        <div class="card-unit">kWh</div>
      </div>
    </div>
    
    <!-- 图表容器 -->
    <div class="charts-grid">
      <!-- 人员密度与能耗关系 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>人员密度与能耗关系</h3>
        </div>
        <div ref="occupancyEnergyChart" class="chart"></div>
      </div>
      
      <!-- 人员密度分布 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>人员密度分布</h3>
        </div>
        <div ref="occupancyDistributionChart" class="chart"></div>
      </div>
      
      <!-- 不同人员密度下的能耗对比 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>不同人员密度下的能耗对比</h3>
        </div>
        <div ref="densityComparisonChart" class="chart"></div>
      </div>
      
      <!-- 人员密度时间趋势 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>人员密度时间趋势</h3>
        </div>
        <div ref="occupancyTrendChart" class="chart"></div>
      </div>
      
      <!-- 人员密度与设备使用关系 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>人员密度与设备使用关系</h3>
        </div>
        <div ref="equipmentUsageChart" class="chart"></div>
      </div>
      
      <!-- 人员活动时间分布 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>人员活动时间分布</h3>
        </div>
        <div ref="activityDistributionChart" class="chart"></div>
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

const occupancyEnergyChart = ref(null)
const occupancyDistributionChart = ref(null)
const densityComparisonChart = ref(null)
const occupancyTrendChart = ref(null)
const equipmentUsageChart = ref(null)
const activityDistributionChart = ref(null)
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
  occupancy_range: 'all'
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
      occupancy_range: form.value.occupancy_range
    }
    
    try {
      const occupancyImpactRes = await queryAPI.getOccupancyImpact(params)
      if (occupancyImpactRes.data?.error) {
        ElMessage.error(`分析失败: ${occupancyImpactRes.data.error}`)
        return
      }
      analysisResult.value = occupancyImpactRes.data
      ElMessage.success('分析完成')
    } catch (apiError) {
      console.error('API调用失败:', apiError)
      ElMessage.error('分析失败，未获取到真实数据')
      return
    }
    
    // 等待DOM更新后渲染图表
    nextTick(() => {
      renderOccupancyEnergyChart()
      renderOccupancyDistributionChart()
      renderDensityComparisonChart()
      renderOccupancyTrendChart()
      renderEquipmentUsageChart()
      renderActivityDistributionChart()
    })
  } catch (error) {
    console.error('分析失败:', error)
    // 错误已在接口分支提示，这里保留上次有效结果
  } finally {
    loading.value = false
  }
}

const DENSITY_LEVEL_META = {
  Low: { label: '低 (0-30%)', density: 0.15 },
  Medium: { label: '中 (30-70%)', density: 0.5 },
  High: { label: '高 (70-100%)', density: 0.85 }
}

const safeSetOption = (chartInstance, option, chartName) => {
  try {
    chartInstance.setOption(option)
  } catch (error) {
    console.error(`${chartName}渲染失败:`, error)
    ElMessage.error(`${chartName}渲染失败，请刷新后重试`)
  }
}

const getOccupancyLevels = () => {
  const impact = analysisResult.value.occupancy_impact || {}
  return ['Low', 'Medium', 'High']
    .filter(level => impact[level] !== undefined && impact[level] !== null)
    .map(level => ({
      level,
      label: DENSITY_LEVEL_META[level].label,
      density: DENSITY_LEVEL_META[level].density,
      energy: Number(impact[level] || 0)
    }))
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
const occupancyCorrelation = computed(() => {
  const correlation = Number(analysisResult.value.correlation)
  return Number.isFinite(correlation) ? correlation.toFixed(2) : '--'
})

const avgOccupancy = computed(() => {
  const levels = getOccupancyLevels()
  if (!levels.length) return '--'
  const totalEnergyValue = levels.reduce((sum, item) => sum + item.energy, 0)
  if (totalEnergyValue <= 0) return '--'
  const weightedDensity = levels.reduce((sum, item) => sum + item.density * item.energy, 0) / totalEnergyValue
  return (weightedDensity * 100).toFixed(1)
})

const perCapitaEnergy = computed(() => '--')

const totalEnergy = computed(() => {
  const levels = getOccupancyLevels()
  if (!levels.length) return '--'
  return Math.round(levels.reduce((sum, item) => sum + item.energy, 0))
})

// 图表渲染函数
const renderOccupancyEnergyChart = () => {
  if (!occupancyEnergyChart.value) return
  if (charts.value.occupancyEnergy) charts.value.occupancyEnergy.dispose()

  charts.value.occupancyEnergy = echarts.init(occupancyEnergyChart.value)
  const levels = getOccupancyLevels()
  if (!levels.length) {
    safeSetOption(charts.value.occupancyEnergy, noDataOption('人员密度与能耗关系'), '人员密度与能耗关系图')
    return
  }

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        return `密度等级: ${params.data.label}<br/>估算密度: ${(params.value[0] * 100).toFixed(1)}%<br/>平均能耗: ${Number(params.value[1]).toFixed(2)}kWh`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '人员密度',
      axisLabel: {
        formatter: value => `${(Number(value) * 100).toFixed(0)}%`
      },
      min: 0,
      max: 1
    },
    yAxis: {
      type: 'value',
      name: '平均能耗(kWh)'
    },
    series: [{
      name: '密度等级能耗',
      type: 'scatter',
      data: levels.map(item => ({
        value: [item.density, item.energy],
        label: item.label
      })),
      symbolSize: 14,
      itemStyle: {
        color: '#4682b4'
      }
    }]
  }

  safeSetOption(charts.value.occupancyEnergy, option, '人员密度与能耗关系图')
}

const renderOccupancyDistributionChart = () => {
  if (!occupancyDistributionChart.value) return
  if (charts.value.occupancyDistribution) charts.value.occupancyDistribution.dispose()

  charts.value.occupancyDistribution = echarts.init(occupancyDistributionChart.value)
  const levels = getOccupancyLevels()
  if (!levels.length) {
    safeSetOption(charts.value.occupancyDistribution, noDataOption('人员密度分布'), '人员密度分布图')
    return
  }

  const total = levels.reduce((sum, item) => sum + item.energy, 0)
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: params => {
        if (!params?.length) return ''
        const p = params[0]
        return `${p.name}<br/>能耗占比: ${Number(p.value).toFixed(2)}%`
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
      data: levels.map(item => item.label)
    },
    yAxis: {
      type: 'value',
      name: '能耗占比(%)'
    },
    series: [{
      name: '能耗占比',
      type: 'bar',
      data: levels.map(item => total > 0 ? (item.energy / total) * 100 : 0),
      itemStyle: { color: '#188df0' }
    }]
  }

  safeSetOption(charts.value.occupancyDistribution, option, '人员密度分布图')
}

const renderDensityComparisonChart = () => {
  if (!densityComparisonChart.value) return
  if (charts.value.densityComparison) charts.value.densityComparison.dispose()

  charts.value.densityComparison = echarts.init(densityComparisonChart.value)
  const levels = getOccupancyLevels()
  if (!levels.length) {
    safeSetOption(charts.value.densityComparison, noDataOption('不同人员密度下的能耗对比'), '密度对比图')
    return
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['平均能耗', '单位密度能耗'],
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
      data: levels.map(item => item.label)
    },
    yAxis: [
      {
        type: 'value',
        name: '平均能耗(kWh)',
        position: 'left'
      },
      {
        type: 'value',
        name: '单位密度能耗',
        position: 'right'
      }
    ],
    series: [
      {
        name: '平均能耗',
        type: 'bar',
        data: levels.map(item => item.energy),
        itemStyle: { color: '#ff6347' }
      },
      {
        name: '单位密度能耗',
        type: 'line',
        yAxisIndex: 1,
        data: levels.map(item => item.density > 0 ? item.energy / item.density : 0),
        itemStyle: { color: '#4682b4' },
        lineStyle: { width: 3 },
        symbol: 'circle',
        symbolSize: 8
      }
    ]
  }

  safeSetOption(charts.value.densityComparison, option, '密度对比图')
}

const renderOccupancyTrendChart = () => {
  if (!occupancyTrendChart.value) return
  if (charts.value.occupancyTrend) charts.value.occupancyTrend.dispose()

  charts.value.occupancyTrend = echarts.init(occupancyTrendChart.value)
  const levels = getOccupancyLevels()
  if (!levels.length) {
    safeSetOption(charts.value.occupancyTrend, noDataOption('人员密度时间趋势'), '人员密度趋势图')
    return
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['估算人员密度', '平均能耗'],
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
      data: levels.map(item => item.label)
    },
    yAxis: [
      {
        type: 'value',
        name: '估算人员密度(%)',
        position: 'left'
      },
      {
        type: 'value',
        name: '平均能耗(kWh)',
        position: 'right'
      }
    ],
    series: [
      {
        name: '估算人员密度',
        type: 'line',
        data: levels.map(item => item.density * 100),
        itemStyle: { color: '#4682b4' },
        lineStyle: { width: 3 }
      },
      {
        name: '平均能耗',
        type: 'bar',
        yAxisIndex: 1,
        data: levels.map(item => item.energy),
        itemStyle: { color: '#ff6347' }
      }
    ]
  }

  safeSetOption(charts.value.occupancyTrend, option, '人员密度趋势图')
}

const renderEquipmentUsageChart = () => {
  if (!equipmentUsageChart.value) return
  if (charts.value.equipmentUsage) charts.value.equipmentUsage.dispose()

  charts.value.equipmentUsage = echarts.init(equipmentUsageChart.value)
  safeSetOption(charts.value.equipmentUsage, noDataOption('人员密度与设备使用关系'), '设备使用关系图')
}

const renderActivityDistributionChart = () => {
  if (!activityDistributionChart.value) return
  if (charts.value.activityDistribution) charts.value.activityDistribution.dispose()

  charts.value.activityDistribution = echarts.init(activityDistributionChart.value)
  safeSetOption(charts.value.activityDistribution, noDataOption('人员活动时间分布'), '活动分布图')
}

// 数据导出
const exportData = (format) => {
  const levels = getOccupancyLevels()
  if (!levels.length) {
    ElMessage.warning('当前无可导出的真实数据')
    return
  }

  let csvContent = '密度等级,估算密度(%),平均能耗(kWh)\n'
  levels.forEach(item => {
    csvContent += `${item.label},${(item.density * 100).toFixed(1)},${item.energy.toFixed(2)}\n`
  })
  
  // 创建下载链接
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `人员影响分析_${new Date().toISOString().split('T')[0]}.${format}`)
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
.occupancy-impact-chart-page {
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