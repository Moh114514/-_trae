<template>
  <div class="intensity-chart-page">
    <div class="card-header">
      <h2>能耗强度分析</h2>
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
        
        <el-form-item label="建筑面积(m²)">
          <el-input-number v-model="form.building_area" :min="100" :max="100000" :step="100" placeholder="建筑面积" style="width: 150px;" />
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
        <div class="card-title">平均能耗强度</div>
        <div class="card-value">{{ avgIntensity }} kWh/m²</div>
      </div>
      <div class="overview-card">
        <div class="card-title">最高能耗强度</div>
        <div class="card-value">{{ maxIntensity }} kWh/m²</div>
      </div>
      <div class="overview-card">
        <div class="card-title">最低能耗强度</div>
        <div class="card-value">{{ minIntensity }} kWh/m²</div>
      </div>
      <div class="overview-card">
        <div class="card-title">总能耗</div>
        <div class="card-value">{{ totalEnergy }} kWh</div>
      </div>
    </div>
    
    <!-- 图表容器 -->
    <div class="charts-grid">
      <!-- 能耗强度趋势图 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>能耗强度趋势</h3>
        </div>
        <div ref="intensityChart" class="chart"></div>
      </div>
      
      <!-- 能耗强度分类分析 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>能耗强度分类分析</h3>
        </div>
        <div ref="categoryChart" class="chart"></div>
      </div>
      
      <!-- 能耗强度对比图 -->
      <div class="chart-item">
        <div class="chart-header">
          <h3>能耗强度对比</h3>
        </div>
        <div ref="comparisonChart" class="chart"></div>
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

const intensityChart = ref(null)
const categoryChart = ref(null)
const comparisonChart = ref(null)
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
  building_area: 1000
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
      building_area: form.value.building_area
    }
    
    try {
      const intensityRes = await queryAPI.getIntensity(params)
      if (intensityRes.data?.error) {
        ElMessage.error(`分析失败: ${intensityRes.data.error}`)
        return
      }
      analysisResult.value = intensityRes.data
      ElMessage.success('分析完成')
    } catch (apiError) {
      console.error('API调用失败:', apiError)
      ElMessage.error('分析失败，未获取到真实数据')
      return
    }
    
    // 等待DOM更新后渲染图表
    nextTick(() => {
      renderIntensityChart()
      renderCategoryChart()
      renderComparisonChart()
    })
  } catch (error) {
    console.error('分析失败:', error)
    // 错误已在接口分支提示，这里保留上次有效结果
  } finally {
    loading.value = false
  }
}

const getDailyIntensity = () => analysisResult.value.daily_intensity_kwh_per_sqm || []

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
const avgIntensity = computed(() => {
  const dailyIntensity = getDailyIntensity()
  if (dailyIntensity.length > 0) {
    const sum = dailyIntensity.reduce((acc, item) => acc + item.intensity, 0)
    return (sum / dailyIntensity.length).toFixed(2)
  }
  return '--'
})

const maxIntensity = computed(() => {
  const dailyIntensity = getDailyIntensity()
  if (dailyIntensity.length > 0) {
    return Math.max(...dailyIntensity.map(item => item.intensity)).toFixed(2)
  }
  return '--'
})

const minIntensity = computed(() => {
  const dailyIntensity = getDailyIntensity()
  if (dailyIntensity.length > 0) {
    return Math.min(...dailyIntensity.map(item => item.intensity)).toFixed(2)
  }
  return '--'
})

const totalEnergy = computed(() => {
  const dailyIntensity = getDailyIntensity()
  if (dailyIntensity.length > 0) {
    const sum = dailyIntensity.reduce((acc, item) => acc + item.intensity, 0)
    return (sum * form.value.building_area).toFixed(0)
  }
  return '--'
})

const renderIntensityChart = () => {
  if (!intensityChart.value) return
  
  if (charts.value.intensity) {
    charts.value.intensity.dispose()
  }
  
  charts.value.intensity = echarts.init(intensityChart.value)
  
  const dailyIntensity = getDailyIntensity()
  if (dailyIntensity.length === 0) {
    safeSetOption(charts.value.intensity, noDataOption('能耗强度趋势'), '能耗强度趋势图')
    return
  }

  const xAxisData = dailyIntensity.map(item => item.date)
  const intensityData = dailyIntensity.map(item => item.intensity)
  
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
          color: '#87ceeb'
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
  
  safeSetOption(charts.value.intensity, option, '能耗强度趋势图')
}



const renderCategoryChart = () => {
  if (!categoryChart.value) return
  
  if (charts.value.category) {
    charts.value.category.dispose()
  }
  
  charts.value.category = echarts.init(categoryChart.value)
  const dailyIntensity = getDailyIntensity()
  if (dailyIntensity.length === 0) {
    safeSetOption(charts.value.category, noDataOption('能耗强度分类分析'), '能耗强度分类图')
    return
  }

  const categories = ['低能耗', '中低能耗', '中能耗', '中高能耗', '高能耗']
  const ranges = ['< 0.5', '0.5-0.8', '0.8-1.2', '1.2-1.5', '> 1.5']
  const bins = [0, 0, 0, 0, 0]
  dailyIntensity.forEach(item => {
    const v = Number(item.intensity)
    if (!Number.isFinite(v)) return
    if (v < 0.5) bins[0] += 1
    else if (v < 0.8) bins[1] += 1
    else if (v < 1.2) bins[2] += 1
    else if (v < 1.5) bins[3] += 1
    else bins[4] += 1
  })
  const total = bins.reduce((a, b) => a + b, 0) || 1
  const distribution = bins.map(item => Number(((item / total) * 100).toFixed(2)))
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        return `${params.name} (${ranges[params.dataIndex]})<br/>占比: ${params.value}%`
      }
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      bottom: 0,
      data: categories.map((cat, index) => `${cat} (${ranges[index]})`)
    },
    series: [
      {
        name: '能耗强度分布',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}\n{d}%'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '18',
            fontWeight: 'bold'
          }
        },
        data: categories.map((cat, index) => ({
          value: distribution[index],
          name: cat
        }))
      }
    ]
  }
  
  safeSetOption(charts.value.category, option, '能耗强度分类图')
}

const renderComparisonChart = () => {
  if (!comparisonChart.value) return
  
  if (charts.value.comparison) {
    charts.value.comparison.dispose()
  }
  
  charts.value.comparison = echarts.init(comparisonChart.value)
  const dailyIntensity = getDailyIntensity()
  if (dailyIntensity.length === 0) {
    safeSetOption(charts.value.comparison, noDataOption('能耗强度对比'), '能耗强度对比图')
    return
  }

  const values = dailyIntensity.map(item => Number(item.intensity)).filter(v => Number.isFinite(v))
  const sorted = [...values].sort((a, b) => a - b)
  const median = sorted[Math.floor(sorted.length / 2)] || 0
  const avg = values.reduce((sum, v) => sum + v, 0) / (values.length || 1)
  const max = Math.max(...values)
  const min = Math.min(...values)

  const xAxisData = ['平均值', '中位值', '最高值', '最低值']
  const currentBuildingIntensity = [avg, median, max, min]
  const baselineIntensity = [avg, avg, avg, avg]
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['当前建筑', '同类平均'],
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
      data: xAxisData
    },
    yAxis: {
      type: 'value',
      name: '能耗强度(kWh/m²)'
    },
    series: [
      {
        name: '当前建筑',
        type: 'bar',
        data: currentBuildingIntensity,
        itemStyle: {
          color: '#87ceeb'
        }
      },
      {
        name: '基准值',
        type: 'line',
        data: baselineIntensity,
        itemStyle: {
          color: '#98fb98'
        },
        lineStyle: {
          width: 3
        },
        symbol: 'circle',
        symbolSize: 8
      }
    ]
  }
  
  safeSetOption(charts.value.comparison, option, '能耗强度对比图')
}

// 数据导出
const exportData = (format) => {
  const exportData = getDailyIntensity()
  if (exportData.length === 0) {
    ElMessage.warning('当前无可导出的真实数据')
    return
  }
  
  // 生成CSV内容
  let csvContent = '日期,能耗强度(kWh/m²)\n'
  exportData.forEach(item => {
    csvContent += `${item.date},${item.intensity.toFixed(2)}\n`
  })
  
  // 创建下载链接
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `能耗强度分析_${new Date().toISOString().split('T')[0]}.${format}`)
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
.intensity-chart-page {
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
  margin-top: 15px;
  display: flex;
  gap: 10px;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.overview-card {
  background-color: #fff;
  padding: 20px;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  text-align: center;
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
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.chart-header {
  margin-bottom: 15px;
  text-align: center;
}

.chart-header h3 {
  font-size: 16px;
  font-weight: bold;
  margin: 0;
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
@media (max-width: 1024px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .overview-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .chart {
    height: 300px;
  }
}

@media (max-width: 480px) {
  .overview-cards {
    grid-template-columns: 1fr;
  }
  
  .time-range-buttons {
    flex-wrap: wrap;
  }
  
  .el-form {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }
  
  .el-form-item {
    margin-bottom: 10px;
  }
}
</style>