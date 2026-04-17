<template>
  <div class="hourly-pattern-chart-page">
    <div class="card-header">
      <h2>小时模式分析</h2>
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
        
        <el-form-item label="日期类型">
          <el-select v-model="form.day_type" placeholder="选择日期类型" style="width: 150px;">
            <el-option label="工作日" value="weekday" />
            <el-option label="周末" value="weekend" />
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
        <div class="card-title">峰值能耗时段</div>
        <div class="card-value">{{ peakEnergyHour }}</div>
        <div class="card-unit">时</div>
      </div>
      <div class="overview-card">
        <div class="card-title">最低能耗时段</div>
        <div class="card-value">{{ lowestEnergyHour }}</div>
        <div class="card-unit">时</div>
      </div>
      <div class="overview-card">
        <div class="card-title">平均能耗</div>
        <div class="card-value">{{ avgEnergy }}</div>
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
      <!-- 小时能耗趋势 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>小时能耗趋势</h3>
        </div>
        <div ref="hourlyTrendChart" class="chart"></div>
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
      
      <!-- 能耗时段分布 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>能耗时段分布</h3>
        </div>
        <div ref="energyDistributionChart" class="chart"></div>
      </div>
      
      <!-- 季节性能耗对比 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>季节性能耗对比</h3>
        </div>
        <div ref="seasonalComparisonChart" class="chart"></div>
      </div>
      
      <!-- 能耗异常检测 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>能耗异常检测</h3>
        </div>
        <div ref="anomalyDetectionChart" class="chart"></div>
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

const hourlyTrendChart = ref(null)
const weekdayWeekendChart = ref(null)
const energyCompositionChart = ref(null)
const energyDistributionChart = ref(null)
const seasonalComparisonChart = ref(null)
const anomalyDetectionChart = ref(null)
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
  day_type: 'all'
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
      day_type: form.value.day_type
    }
    
    try {
      const hourlyPatternRes = await queryAPI.getHourlyPattern(params)
      if (hourlyPatternRes.data?.error) {
        ElMessage.error(`分析失败: ${hourlyPatternRes.data.error}`)
        return
      }
      analysisResult.value = hourlyPatternRes.data
      ElMessage.success('分析完成')
    } catch (apiError) {
      console.error('API调用失败:', apiError)
      ElMessage.error('分析失败，未获取到真实数据')
      return
    }
    
    // 等待DOM更新后渲染图表
    nextTick(() => {
      renderHourlyTrendChart()
      renderWeekdayWeekendChart()
      renderEnergyCompositionChart()
      renderEnergyDistributionChart()
      renderSeasonalComparisonChart()
      renderAnomalyDetectionChart()
    })
  } catch (error) {
    console.error('分析失败:', error)
    // 错误已在接口分支提示，这里保留上次有效结果
  } finally {
    loading.value = false
  }
}

const getHourlySeries = () => {
  const pattern = analysisResult.value.hourly_pattern || {}
  return Array.from({ length: 24 }, (_, hour) => {
    const item = pattern[String(hour)] || {}
    const electricity = Number(item.electricity_kwh || 0)
    const hvac = Number(item.hvac_kwh || 0)
    const water = Number(item.water_m3 || 0)
    return {
      hour,
      label: `${hour}:00`,
      electricity,
      hvac,
      water,
      total: electricity + hvac
    }
  })
}

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
const peakEnergyHour = computed(() => {
  const series = getHourlySeries().filter(item => item.total > 0)
  if (series.length === 0) return '--'
  return series.reduce((max, item) => (item.total > max.total ? item : max)).hour
})

const lowestEnergyHour = computed(() => {
  const series = getHourlySeries().filter(item => item.total > 0)
  if (series.length === 0) return '--'
  return series.reduce((min, item) => (item.total < min.total ? item : min)).hour
})

const avgEnergy = computed(() => {
  const series = getHourlySeries().filter(item => item.total > 0)
  if (series.length === 0) return '--'
  const avg = series.reduce((sum, item) => sum + item.total, 0) / series.length
  return avg.toFixed(2)
})

const totalEnergy = computed(() => {
  const series = getHourlySeries().filter(item => item.total > 0)
  if (series.length === 0) return '--'
  return Math.round(series.reduce((sum, item) => sum + item.total, 0))
})

// 图表渲染函数
const renderHourlyTrendChart = () => {
  if (!hourlyTrendChart.value) return
  if (charts.value.hourlyTrend) charts.value.hourlyTrend.dispose()
  charts.value.hourlyTrend = echarts.init(hourlyTrendChart.value)

  const series = getHourlySeries()
  const hasData = series.some(item => item.total > 0)
  if (!hasData) {
    safeSetOption(charts.value.hourlyTrend, noDataOption('小时能耗趋势'), '小时能耗趋势图')
    return
  }

  const option = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: { data: ['电力消耗', 'HVAC能耗', '总能耗'], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: { type: 'category', data: series.map(item => item.label), axisLabel: { interval: 2 } },
    yAxis: { type: 'value', name: '能耗(kWh)' },
    series: [
      {
        name: '电力消耗',
        type: 'line',
        data: series.map(item => item.electricity),
        smooth: true,
        itemStyle: { color: '#ff7f50' },
        lineStyle: { width: 3 }
      },
      {
        name: 'HVAC能耗',
        type: 'line',
        data: series.map(item => item.hvac),
        smooth: true,
        itemStyle: { color: '#4682b4' },
        lineStyle: { width: 3 }
      },
      {
        name: '总能耗',
        type: 'line',
        data: series.map(item => item.total),
        smooth: true,
        itemStyle: { color: '#ff6b6b' },
        lineStyle: { width: 3 }
      }
    ]
  }

  safeSetOption(charts.value.hourlyTrend, option, '小时能耗趋势图')
}

const renderWeekdayWeekendChart = () => {
  if (!weekdayWeekendChart.value) return
  if (charts.value.weekdayWeekend) charts.value.weekdayWeekend.dispose()
  charts.value.weekdayWeekend = echarts.init(weekdayWeekendChart.value)

  const series = getHourlySeries()
  const hasData = series.some(item => item.total > 0)
  if (!hasData) {
    safeSetOption(charts.value.weekdayWeekend, noDataOption('工作日vs周末对比'), '工作日周末对比图')
    return
  }

  const daytime = series.map(item => (item.hour >= 8 && item.hour <= 18 ? item.total : null))
  const nighttime = series.map(item => (item.hour < 8 || item.hour > 18 ? item.total : null))

  const option = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['工作时段', '非工作时段'], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: { type: 'category', data: series.map(item => item.label), axisLabel: { interval: 2 } },
    yAxis: { type: 'value', name: '能耗(kWh)' },
    series: [
      { name: '工作时段', type: 'bar', data: daytime, itemStyle: { color: '#4682b4' } },
      { name: '非工作时段', type: 'bar', data: nighttime, itemStyle: { color: '#ff7f50' } }
    ]
  }

  safeSetOption(charts.value.weekdayWeekend, option, '工作日周末对比图')
}

const renderEnergyCompositionChart = () => {
  if (!energyCompositionChart.value) return
  if (charts.value.energyComposition) charts.value.energyComposition.dispose()
  charts.value.energyComposition = echarts.init(energyCompositionChart.value)

  const series = getHourlySeries()
  const electricity = series.reduce((sum, item) => sum + item.electricity, 0)
  const hvac = series.reduce((sum, item) => sum + item.hvac, 0)
  const water = series.reduce((sum, item) => sum + item.water, 0)
  if (electricity + hvac + water === 0) {
    safeSetOption(charts.value.energyComposition, noDataOption('能耗构成分析'), '能耗构成图')
    return
  }

  const option = {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', left: 'left', data: ['电力', 'HVAC', '用水'] },
    series: [{
      name: '能耗构成',
      type: 'pie',
      radius: '60%',
      center: ['50%', '50%'],
      data: [
        { value: electricity, name: '电力' },
        { value: hvac, name: 'HVAC' },
        { value: water, name: '用水' }
      ],
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      }
    }]
  }

  safeSetOption(charts.value.energyComposition, option, '能耗构成图')
}

const renderEnergyDistributionChart = () => {
  if (!energyDistributionChart.value) return
  if (charts.value.energyDistribution) charts.value.energyDistribution.dispose()
  charts.value.energyDistribution = echarts.init(energyDistributionChart.value)

  const series = getHourlySeries()
  const total = series.reduce((sum, item) => sum + item.total, 0)
  if (total === 0) {
    safeSetOption(charts.value.energyDistribution, noDataOption('能耗时段分布'), '能耗时段分布图')
    return
  }

  const slots = [
    { label: '00:00-06:00', from: 0, to: 5 },
    { label: '06:00-09:00', from: 6, to: 8 },
    { label: '09:00-12:00', from: 9, to: 11 },
    { label: '12:00-14:00', from: 12, to: 13 },
    { label: '14:00-18:00', from: 14, to: 17 },
    { label: '18:00-24:00', from: 18, to: 23 }
  ]
  const data = slots.map(slot => {
    const slotTotal = series
      .filter(item => item.hour >= slot.from && item.hour <= slot.to)
      .reduce((sum, item) => sum + item.total, 0)
    return Number(((slotTotal / total) * 100).toFixed(2))
  })

  const option = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: { type: 'category', data: slots.map(slot => slot.label), axisLabel: { rotate: 45 } },
    yAxis: { type: 'value', name: '能耗占比(%)' },
    series: [{
      name: '能耗占比',
      type: 'bar',
      data,
      itemStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [{ offset: 0, color: '#ff7f50' }, { offset: 1, color: '#ff6b6b' }]
        }
      }
    }]
  }

  safeSetOption(charts.value.energyDistribution, option, '能耗时段分布图')
}

const renderSeasonalComparisonChart = () => {
  if (!seasonalComparisonChart.value) return
  if (charts.value.seasonalComparison) charts.value.seasonalComparison.dispose()
  charts.value.seasonalComparison = echarts.init(seasonalComparisonChart.value)
  safeSetOption(charts.value.seasonalComparison, noDataOption('季节性能耗对比'), '季节性能耗图')
}

const renderAnomalyDetectionChart = () => {
  if (!anomalyDetectionChart.value) return
  if (charts.value.anomalyDetection) charts.value.anomalyDetection.dispose()
  charts.value.anomalyDetection = echarts.init(anomalyDetectionChart.value)

  const series = getHourlySeries()
  const totals = series.map(item => item.total)
  const validTotals = totals.filter(value => value > 0)
  if (validTotals.length === 0) {
    safeSetOption(charts.value.anomalyDetection, noDataOption('能耗异常检测'), '能耗异常检测图')
    return
  }

  const mean = validTotals.reduce((sum, value) => sum + value, 0) / validTotals.length
  const variance = validTotals.reduce((sum, value) => sum + ((value - mean) ** 2), 0) / validTotals.length
  const std = Math.sqrt(variance)
  const threshold = mean + std * 2
  const anomalyData = totals.map((value, idx) => (value > threshold ? [idx, value] : [idx, null]))

  const option = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: { data: ['能耗', '异常值', '阈值'], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: { type: 'category', data: series.map(item => item.label), axisLabel: { interval: 2 } },
    yAxis: { type: 'value', name: '能耗(kWh)' },
    series: [
      {
        name: '能耗',
        type: 'line',
        data: totals,
        smooth: true,
        itemStyle: { color: '#4682b4' }
      },
      {
        name: '异常值',
        type: 'scatter',
        data: anomalyData,
        symbolSize: 15,
        itemStyle: { color: '#ff6b6b' }
      },
      {
        name: '阈值',
        type: 'line',
        data: Array.from({ length: 24 }, () => Number(threshold.toFixed(2))),
        lineStyle: { type: 'dashed', color: '#ff9800' },
        symbol: 'none'
      }
    ]
  }

  safeSetOption(charts.value.anomalyDetection, option, '能耗异常检测图')
}

// 数据导出
const exportData = (format) => {
  const exportData = getHourlySeries().filter(item => item.total > 0 || item.water > 0)
  if (exportData.length === 0) {
    ElMessage.warning('当前无可导出的真实数据')
    return
  }
  
  // 生成CSV内容
  let csvContent = '小时,电力消耗(kWh),HVAC能耗(kWh),总能耗(kWh)\n'
  exportData.forEach(item => {
    csvContent += `${item.label},${item.electricity.toFixed(2)},${item.hvac.toFixed(2)},${item.total.toFixed(2)}\n`
  })
  
  // 创建下载链接
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `小时模式分析_${new Date().toISOString().split('T')[0]}.${format}`)
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
.hourly-pattern-chart-page {
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