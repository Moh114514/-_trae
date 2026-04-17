<template>
  <div class="peak-demand-chart-page">
    <div class="card-header">
      <h2>峰值需求分析</h2>
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
        
        <el-form-item>
          <el-button type="primary" @click="handleAnalyze">开始分析</el-button>
        </el-form-item>
      </el-form>
      
      <div class="quick-time-select">
        <el-button size="large" @click="setTimeRange('today')" :type="selectedRange === 'today' ? 'primary' : 'default'">今天</el-button>
        <el-button size="large" @click="setTimeRange('week')" :type="selectedRange === 'week' ? 'primary' : 'default'">本周</el-button>
        <el-button size="large" @click="setTimeRange('month')" :type="selectedRange === 'month' ? 'primary' : 'default'">本月</el-button>
        <el-button size="large" @click="setTimeRange('year')" :type="selectedRange === 'year' ? 'primary' : 'default'">本年</el-button>
      </div>
    </div>
    
    <!-- 数据概览卡片 -->
    <div class="overview-cards">
      <el-card class="overview-card">
        <div class="card-content">
          <div class="card-title">最大峰值</div>
          <div class="card-value">{{ maxPeak }}</div>
          <div class="card-unit">kWh</div>
        </div>
      </el-card>
      <el-card class="overview-card">
        <div class="card-content">
          <div class="card-title">峰值出现时间</div>
          <div class="card-value">{{ peakTime }}</div>
          <div class="card-unit"></div>
        </div>
      </el-card>
      <el-card class="overview-card">
        <div class="card-content">
          <div class="card-title">平均需求</div>
          <div class="card-value">{{ avgDemand }}</div>
          <div class="card-unit">kWh</div>
        </div>
      </el-card>
      <el-card class="overview-card">
        <div class="card-content">
          <div class="card-title">峰值负荷率</div>
          <div class="card-value">{{ peakLoadRate }}</div>
          <div class="card-unit">%</div>
        </div>
      </el-card>
    </div>
    
    <!-- 图表容器 -->
    <div class="charts-grid">
      <div class="chart-item">
        <h3>小时峰值分布</h3>
        <div ref="peakDemandChart" class="chart"></div>
      </div>
      <div class="chart-item">
        <h3>周峰值对比</h3>
        <div ref="weeklyPeakChart" class="chart"></div>
      </div>
      <div class="chart-item">
        <h3>峰值时段分析</h3>
        <div ref="peakTimeChart" class="chart"></div>
      </div>
    </div>
    
    <!-- 导出按钮 -->
    <div class="export-buttons">
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

// 图表引用
const peakDemandChart = ref(null)
const weeklyPeakChart = ref(null)
const peakTimeChart = ref(null)
const charts = ref({})

// 数据和状态
const buildings = ref([])
const loading = ref(false)
const analysisResult = ref({})
const selectedDays = ref(7)
const selectedRange = ref('week')

// 设置默认时间范围为包含数据库中数据的时间范围
const startDate = new Date('2021-01-01')
const endDate = new Date('2021-01-31')

const form = ref({
  building_id: '',
  start_time: startDate.toISOString().slice(0, 19).replace('T', ' '),
  end_time: endDate.toISOString().slice(0, 19).replace('T', ' ')
})

// 计算属性 - 数据概览
const maxPeak = computed(() => {
  const hourlyProfile = analysisResult.value.hourly_profile || {}
  const peakData = Object.values(hourlyProfile)
  if (peakData.length > 0) {
    return Math.max(...peakData).toFixed(2)
  }
  return '0.00'
})

const peakTime = computed(() => {
  const hourlyProfile = analysisResult.value.hourly_profile || {}
  if (Object.keys(hourlyProfile).length > 0) {
    let maxHour = '0'
    let maxValue = 0
    for (const [hour, value] of Object.entries(hourlyProfile)) {
      if (value > maxValue) {
        maxValue = value
        maxHour = hour
      }
    }
    return `${maxHour}:00`
  }
  return '--'
})

const avgDemand = computed(() => {
  const hourlyProfile = analysisResult.value.hourly_profile || {}
  const peakData = Object.values(hourlyProfile)
  if (peakData.length > 0) {
    return (peakData.reduce((a, b) => a + b, 0) / peakData.length).toFixed(2)
  }
  return '0.00'
})

const peakLoadRate = computed(() => {
  const hourlyProfile = analysisResult.value.hourly_profile || {}
  const peakData = Object.values(hourlyProfile)
  if (peakData.length > 0) {
    const max = Math.max(...peakData)
    const avg = peakData.reduce((a, b) => a + b, 0) / peakData.length
    return ((max / avg) * 100).toFixed(2)
  }
  return '0.00'
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
    default:
      days = 7
  }
  
  form.value.start_time = start.toISOString().slice(0, 19).replace('T', ' ')
  form.value.end_time = end.toISOString().slice(0, 19).replace('T', ' ')
  // 存储当前选择的天数，用于图表标题与维度切换
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
      end_time: form.value.end_time
    }
    
    try {
      const peakDemandRes = await queryAPI.getPeakDemand(params)
      if (peakDemandRes.data?.error) {
        ElMessage.error(`分析失败: ${peakDemandRes.data.error}`)
        return
      }
      analysisResult.value = peakDemandRes.data
      ElMessage.success('分析完成')
    } catch (apiError) {
      console.error('API调用失败:', apiError)
      ElMessage.error('分析失败，未获取到真实数据')
      return
    }
    
    // 等待DOM更新后渲染图表
    nextTick(() => {
      renderPeakDemandChart()
      renderWeeklyPeakChart()
      renderPeakTimeChart()
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

const renderPeakDemandChart = () => {
  if (!peakDemandChart.value) return
  
  if (charts.value.peakDemand) {
    charts.value.peakDemand.dispose()
  }
  
  charts.value.peakDemand = echarts.init(peakDemandChart.value)
  
  const hourlyProfile = analysisResult.value.hourly_profile || {}
  const xAxisData = Object.keys(hourlyProfile).sort((a, b) => parseInt(a, 10) - parseInt(b, 10))
  const peakData = xAxisData.map(hour => Number(hourlyProfile[hour] || 0))
  const hasData = xAxisData.length > 0
  const title = hasData ? '小时峰值分布' : '小时峰值分布（暂无数据）'
  
  const option = {
    title: {
      text: title,
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        if (!params?.length) return ''
        const value = Number(params[0].value || 0)
        return `${params[0].name}:00<br/>${params[0].seriesName}: ${value.toFixed(2)} kWh`
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
      name: '小时',
      axisLabel: {
        interval: 1
      }
    },
    yAxis: {
      type: 'value',
      name: '电力消耗(kWh)'
    },
    series: [
      {
        name: '小时平均消耗',
        type: 'bar',
        data: peakData,
        itemStyle: {
          color: '#ff7f50'
        },
        markPoint: {
          data: hasData ? [{ type: 'max', name: '最大峰值' }] : []
        }
      }
    ]
  }
  
  safeSetOption(charts.value.peakDemand, option, '小时峰值分布图')
}

// 渲染周峰值对比图
const renderWeeklyPeakChart = () => {
  if (!weeklyPeakChart.value) return
  
  if (charts.value.weeklyPeak) {
    charts.value.weeklyPeak.dispose()
  }
  
  charts.value.weeklyPeak = echarts.init(weeklyPeakChart.value)
  const days = selectedDays.value || 1
  const hourlyProfile = analysisResult.value.hourly_profile || {}
  const dailyPeak = analysisResult.value.daily_peak_data || []

  let title = '峰值需求对比'
  let xAxisData = []
  let peakData = []
  let avgData = []

  if (days === 1) {
    title = '今日小时能耗对比'
    xAxisData = Object.keys(hourlyProfile)
      .sort((a, b) => parseInt(a, 10) - parseInt(b, 10))
      .map(h => `${h}:00`)
    peakData = Object.keys(hourlyProfile)
      .sort((a, b) => parseInt(a, 10) - parseInt(b, 10))
      .map(h => Number(hourlyProfile[h] || 0))
  } else {
    title = days <= 7 ? '近7日峰值对比' : (days <= 31 ? '近30日峰值对比' : '近365日峰值对比')
    xAxisData = dailyPeak.map(item => item.date)
    peakData = dailyPeak.map(item => Number(item.peak || 0))
  }

  if (peakData.length > 0) {
    let sum = 0
    avgData = peakData.map((value, idx) => {
      sum += value
      return sum / (idx + 1)
    })
  }
  
  const option = {
    title: {
      text: title,
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['峰值需求', '平均需求'],
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
        rotate: xAxisData.length > 7 ? 45 : 0
      }
    },
    yAxis: {
      type: 'value',
      name: '电力消耗(kWh)'
    },
    series: [
      {
        name: '峰值需求',
        type: 'bar',
        data: peakData,
        itemStyle: {
          color: '#ff7f50'
        }
      },
      {
        name: '平均需求',
        type: 'line',
        data: avgData,
        smooth: true,
        itemStyle: {
          color: '#4169e1'
        }
      }
    ]
  }
  
  safeSetOption(charts.value.weeklyPeak, option, '周峰值对比图')
}

// 渲染峰值时段分析图
const renderPeakTimeChart = () => {
  if (!peakTimeChart.value) return
  
  if (charts.value.peakTime) {
    charts.value.peakTime.dispose()
  }
  
  charts.value.peakTime = echarts.init(peakTimeChart.value)

  const timeRanges = ['00:00-06:00', '06:00-10:00', '10:00-16:00', '16:00-22:00', '22:00-24:00']
  const hourlyProfile = analysisResult.value.hourly_profile || {}
  const title = Object.keys(hourlyProfile).length > 0 ? '峰值时段分析' : '峰值时段分析（暂无数据）'
  const peakDistribution = [0, 0, 0, 0, 0]

  Object.entries(hourlyProfile).forEach(([hourStr, value]) => {
    const hour = parseInt(hourStr, 10)
    const consumption = Number(value || 0)
    if (hour >= 0 && hour < 6) peakDistribution[0] += consumption
    else if (hour < 10) peakDistribution[1] += consumption
    else if (hour < 16) peakDistribution[2] += consumption
    else if (hour < 22) peakDistribution[3] += consumption
    else peakDistribution[4] += consumption
  })
  
  const option = {
    title: {
      text: title,
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}%'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      bottom: 0
    },
    series: [
      {
        name: '峰值分布',
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
        data: timeRanges.map((range, index) => ({
          value: peakDistribution[index],
          name: range
        }))
      }
    ]
  }
  
  safeSetOption(charts.value.peakTime, option, '峰值时段分析图')
}

// 数据导出
const exportData = (format) => {
  const hourlyProfile = analysisResult.value.hourly_profile || {}
  if (Object.keys(hourlyProfile).length === 0) {
    ElMessage.warning('当前无可导出的真实数据')
    return
  }

  const exportData = Object.entries(hourlyProfile).map(([hour, value]) => ({
    hour: `${hour}:00`,
    value: Number(value || 0)
  }))
  
  // 生成CSV数据
  let csvContent = '小时,能耗值\n'
  
  exportData.forEach(item => {
    csvContent += `${item.hour},${item.value}\n`
  })
  
  // 创建下载链接
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute('download', `峰值需求分析_${form.value.building_id}_${new Date().toISOString().split('T')[0]}.${format}`)
  document.body.appendChild(link)
  
  // 触发下载
  link.click()
  
  // 清理
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  ElMessage.success('数据导出成功')
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
.peak-demand-chart-page {
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.quick-time-select {
  display: flex;
  gap: 10px;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.overview-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.overview-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 20px 0 rgba(0, 0, 0, 0.15);
}

.card-content {
  text-align: center;
  padding: 20px;
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
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 30px;
  margin-bottom: 30px;
}

.chart-item {
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.chart-item h3 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.chart {
  width: 100%;
  height: 350px;
}

.export-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .chart-controls {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .quick-time-select {
    width: 100%;
    justify-content: space-between;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .overview-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media screen and (max-width: 480px) {
  .overview-cards {
    grid-template-columns: 1fr;
  }
  
  .chart-item {
    padding: 15px;
  }
  
  .chart {
    height: 300px;
  }
}
</style>