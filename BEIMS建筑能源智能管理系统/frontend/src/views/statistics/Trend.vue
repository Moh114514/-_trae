<template>
  <div class="trend-chart-page">
    <div class="card-header">
      <h2>能耗趋势</h2>
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
        
        <el-form-item label="指标">
          <el-select v-model="form.metric" placeholder="选择指标" style="width: 150px;">
            <el-option label="电力消耗" value="electricity_kwh" />
            <el-option label="用水量" value="water_m3" />
            <el-option label="HVAC能耗" value="hvac_kwh" />
          </el-select>
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
          <div class="card-title">总能耗</div>
          <div class="card-value">{{ totalEnergy }}</div>
          <div class="card-unit">{{ unit }}</div>
        </div>
      </el-card>
      <el-card class="overview-card">
        <div class="card-content">
          <div class="card-title">平均能耗</div>
          <div class="card-value">{{ avgEnergy }}</div>
          <div class="card-unit">{{ unit }}</div>
        </div>
      </el-card>
      <el-card class="overview-card">
        <div class="card-content">
          <div class="card-title">最高能耗</div>
          <div class="card-value">{{ maxEnergy }}</div>
          <div class="card-unit">{{ unit }}</div>
        </div>
      </el-card>
      <el-card class="overview-card">
        <div class="card-content">
          <div class="card-title">最低能耗</div>
          <div class="card-value">{{ minEnergy }}</div>
          <div class="card-unit">{{ unit }}</div>
        </div>
      </el-card>
    </div>
    
    <!-- 图表容器 -->
    <div class="charts-grid">
      <div class="chart-item">
        <h3>能耗趋势</h3>
        <div ref="trendChart" class="chart"></div>
      </div>
      <div class="chart-item">
        <h3>能耗分布</h3>
        <div ref="distributionChart" class="chart"></div>
      </div>
      <div class="chart-item">
        <h3>能耗对比</h3>
        <div ref="comparisonChart" class="chart"></div>
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
import { ref, onMounted, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { dataAPI, queryAPI } from '@/api'

// 图表引用
const trendChart = ref(null)
const distributionChart = ref(null)
const comparisonChart = ref(null)
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
  end_time: endDate.toISOString().slice(0, 19).replace('T', ' '),
  metric: 'electricity_kwh'
})

// 计算属性 - 数据概览
const unit = computed(() => {
  return form.value.metric === 'electricity_kwh' ? 'kWh' : form.value.metric === 'water_m3' ? 'm³' : 'kWh'
})

const energyData = computed(() => {
  const dailyData = analysisResult.value.daily_data || []
  const data = dailyData.map(item => item[form.value.metric])
  return data
})

const totalEnergy = computed(() => {
  const data = energyData.value
  return data.length > 0 ? data.reduce((a, b) => a + b, 0).toFixed(2) : '0.00'
})

const avgEnergy = computed(() => {
  const data = energyData.value
  return data.length > 0 ? (data.reduce((a, b) => a + b, 0) / data.length).toFixed(2) : '0.00'
})

const maxEnergy = computed(() => {
  const data = energyData.value
  return data.length > 0 ? Math.max(...data).toFixed(2) : '0.00'
})

const minEnergy = computed(() => {
  const data = energyData.value
  return data.length > 0 ? Math.min(...data).toFixed(2) : '0.00'
})

// 加载建筑列表
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

// 数据分析
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
      metric: form.value.metric
    }
    
    try {
      const trendRes = await queryAPI.getTrend(params)
      if (trendRes.data?.error) {
        ElMessage.error(`分析失败: ${trendRes.data.error}`)
        return
      }
      analysisResult.value = trendRes.data
      ElMessage.success('分析完成')
    } catch (apiError) {
      console.error('API调用失败:', apiError)
      ElMessage.error('分析失败，未获取到真实数据')
      return
    }
    
    // 等待DOM更新后渲染图表
    nextTick(() => {
      renderTrendChart()
      renderDistributionChart()
      renderComparisonChart()
    })
  } catch (error) {
    console.error('分析失败:', error)
    // 错误已在接口分支提示，这里保留上次有效结果
  } finally {
    loading.value = false
  }
}

// 渲染能耗趋势图
const renderTrendChart = () => {
  if (!trendChart.value) return
  
  if (charts.value.trend) {
    charts.value.trend.dispose()
  }
  
  charts.value.trend = echarts.init(trendChart.value)
  
  const dailyData = analysisResult.value.daily_data || []
  const xAxisData = dailyData.map(item => item.timestamp)
  const yData = dailyData.map(item => item[form.value.metric])
  
  if (xAxisData.length === 0) {
    // 暂无数据时显示空提示
    const option = {
      graphic: {
        elements: [
          {
            type: 'text',
            left: 'center',
            top: 'center',
            style: {
              text: '暂无可用数据',
              fontSize: 14,
              fill: '#999'
            }
          }
        ]
      }
    }
    charts.value.trend.setOption(option)
    return
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        let result = params[0].name + '<br/>';
        result += params[0].seriesName + ': ' + params[0].value + ' ' + unit.value + '<br/>';
        if (params.length > 1) {
          result += params[1].seriesName + ': ' + params[1].value.toFixed(2) + ' ' + unit.value;
        }
        return result;
      }
    },
    legend: {
      data: ['能耗值', '7天移动平均'],
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
      data: xAxisData,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: form.value.metric === 'electricity_kwh' ? '电力消耗(kWh)' : form.value.metric === 'water_m3' ? '用水量(m³)' : 'HVAC能耗(kWh)'
    },
    series: [
      {
        name: '能耗值',
        type: 'line',
        data: yData,
        smooth: true,
        itemStyle: {
          color: '#4169e1'
        },
        markPoint: {
          data: [
            { type: 'max', name: '最大值' },
            { type: 'min', name: '最小值' }
          ]
        }
      },
      {
        name: '7天移动平均',
        type: 'line',
        data: yData.map((_, i) => yData.slice(Math.max(0, i-6), i+1).reduce((a, b) => a + b, 0) / Math.min(7, i+1)),
        smooth: true,
        itemStyle: {
          color: '#ff7f50'
        }
      }
    ]
  }
  
  charts.value.trend.setOption(option)
}

// 渲染能耗分布图
const renderDistributionChart = () => {
  if (!distributionChart.value) return
  
  if (charts.value.distribution) {
    charts.value.distribution.dispose()
  }
  
  charts.value.distribution = echarts.init(distributionChart.value)
  
  const dailyData = analysisResult.value.daily_data || []
  let energyData = dailyData.map(item => item[form.value.metric])
  
  if (energyData.length === 0) {
    // 暂无数据时显示空提示
    const option = {
      graphic: {
        elements: [
          {
            type: 'text',
            left: 'center',
            top: 'center',
            style: {
              text: '暂无可用数据',
              fontSize: 14,
              fill: '#999'
            }
          }
        ]
      }
    }
    charts.value.distribution.setOption(option)
    return
  }
  
  // 计算直方图数据
  const binCount = 10
  const min = Math.min(...energyData)
  const max = Math.max(...energyData)
  const binWidth = (max - min) / binCount
  const histogramData = new Array(binCount).fill(0)
  
  energyData.forEach(value => {
    const binIndex = Math.min(Math.floor((value - min) / binWidth), binCount - 1)
    histogramData[binIndex]++
  })
  
  const xAxisData = []
  for (let i = 0; i < binCount; i++) {
    const start = min + i * binWidth
    const end = min + (i + 1) * binWidth
    xAxisData.push(`${start.toFixed(1)}-${end.toFixed(1)}`)
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
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
      name: '频率'
    },
    series: [
      {
        name: '能耗分布',
        type: 'bar',
        data: histogramData,
        itemStyle: {
          color: '#87ceeb'
        }
      }
    ]
  }
  
  charts.value.distribution.setOption(option)
}

// 渲染能耗对比图
const renderComparisonChart = () => {
  if (!comparisonChart.value) return
  
  if (charts.value.comparison) {
    charts.value.comparison.dispose()
  }
  
  charts.value.comparison = echarts.init(comparisonChart.value)
  
  const dailyData = analysisResult.value.daily_data || []
  
  if (dailyData.length < 14) {
    // 数据不足以进行对比时显示空提示
    const option = {
      graphic: {
        elements: [
          {
            type: 'text',
            left: 'center',
            top: 'center',
            style: {
              text: '需要至少14天的数据进行对比',
              fontSize: 14,
              fill: '#999'
            }
          }
        ]
      }
    }
    charts.value.comparison.setOption(option)
    return
  }
  
  const midPoint = Math.floor(dailyData.length / 2)
  const currentPeriod = dailyData.slice(midPoint)
  const previousPeriod = dailyData.slice(0, midPoint)
  
  const labels = currentPeriod.map((_, i) => `Day ${i + 1}`)
  const currentData = currentPeriod.map(item => item[form.value.metric])
  const previousData = previousPeriod.length >= currentPeriod.length
    ? previousPeriod.slice(-currentPeriod.length).map(item => item[form.value.metric])
    : previousPeriod.map(item => item[form.value.metric])
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['当前周期', '上一周期'],
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
      data: labels,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: form.value.metric === 'electricity_kwh' ? '电力消耗(kWh)' : form.value.metric === 'water_m3' ? '用水量(m³)' : 'HVAC能耗(kWh)'
    },
    series: [
      {
        name: '当前周期',
        type: 'bar',
        data: currentData,
        itemStyle: {
          color: '#4169e1'
        }
      },
      {
        name: '上一周期',
        type: 'bar',
        data: previousData,
        itemStyle: {
          color: '#9370db'
        }
      }
    ]
  }
  
  charts.value.comparison.setOption(option)
}

// 数据导出
const exportData = (format) => {
  const dailyData = analysisResult.value.daily_data || []
  let exportData = []
  
  if (dailyData.length > 0) {
    // 使用API返回的数据
    exportData = dailyData.map(item => ({
      timestamp: item.timestamp,
      value: item[form.value.metric]
    }))
  } else {
    // 使用默认生成的数据
    const data = energyData.value
    if (data.length === 0) {
      ElMessage.warning('没有数据可导出')
      return
    }
    
    // 生成时间戳数据
    const now = new Date('2021-07-01')
    exportData = data.map((value, index) => {
      const date = new Date(now)
      date.setDate(date.getDate() - (data.length - 1 - index))
      return {
        timestamp: date.toISOString().split('T')[0],
        value: value
      }
    })
  }
  
  // 生成CSV数据
  let csvContent = '日期,能耗值\n'
  
  exportData.forEach(item => {
    csvContent += `${item.timestamp},${item.value}\n`
  })
  
  // 创建下载链接
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute('download', `能耗趋势_${form.value.building_id}_${form.value.metric}_${new Date().toISOString().split('T')[0]}.${format}`)
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
  handleAnalyze()
})
</script>

<style scoped>
.trend-chart-page {
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