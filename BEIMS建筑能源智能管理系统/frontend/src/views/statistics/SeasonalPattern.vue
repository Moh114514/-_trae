<template>
  <div class="seasonal-pattern-chart-page">
    <div class="card-header">
      <h2>季节性分析</h2>
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
        
        <el-form-item label="年份">
          <el-select v-model="form.year" placeholder="选择年份" style="width: 150px;">
            <el-option label="2021" value="2021" />
            <el-option label="2022" value="2022" />
            <el-option label="2023" value="2023" />
            <el-option label="全部" value="all" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleAnalyze">开始分析</el-button>
        </el-form-item>
      </el-form>
    </div>
    
    <!-- 数据概览卡片 -->
    <div class="overview-cards">
      <div class="overview-card">
        <div class="card-title">春季平均能耗</div>
        <div class="card-value">{{ springAvgEnergy }}</div>
        <div class="card-unit">kWh</div>
      </div>
      <div class="overview-card">
        <div class="card-title">夏季平均能耗</div>
        <div class="card-value">{{ summerAvgEnergy }}</div>
        <div class="card-unit">kWh</div>
      </div>
      <div class="overview-card">
        <div class="card-title">秋季平均能耗</div>
        <div class="card-value">{{ autumnAvgEnergy }}</div>
        <div class="card-unit">kWh</div>
      </div>
      <div class="overview-card">
        <div class="card-title">冬季平均能耗</div>
        <div class="card-value">{{ winterAvgEnergy }}</div>
        <div class="card-unit">kWh</div>
      </div>
      <div class="overview-card">
        <div class="card-title">年度总能耗</div>
        <div class="card-value">{{ annualTotalEnergy }}</div>
        <div class="card-unit">kWh</div>
      </div>
    </div>
    
    <div class="chart-container">
      <div ref="seasonalChart" class="chart"></div>
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

const seasonalChart = ref(null)
const charts = ref({})
const buildings = ref([])
const loading = ref(false)
const analysisResult = ref({})
const selectedRange = ref('year')
const selectedDays = ref(365)

// 设置默认时间范围为包含数据库中数据的时间范围
const startDate = new Date('2021-01-01')
const endDate = new Date('2021-01-31')

const form = ref({
  building_id: '',
  start_time: startDate.toISOString().slice(0, 19).replace('T', ' '),
  end_time: endDate.toISOString().slice(0, 19).replace('T', ' '),
  year: 'all'
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

// 时间范围设置（默认全年）
const setTimeRange = () => {
  // 设置默认时间范围为2021年全年
  const start = new Date(2021, 0, 1)
  const end = new Date(2021, 11, 31, 23, 59, 59)
  const days = 365
  
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
      year: form.value.year
    }
    
    try {
      const seasonalPatternRes = await queryAPI.getSeasonal(params)
      if (seasonalPatternRes.data?.error) {
        ElMessage.error(`分析失败: ${seasonalPatternRes.data.error}`)
        return
      }
      analysisResult.value = seasonalPatternRes.data
      ElMessage.success('分析完成')
    } catch (apiError) {
      console.error('API调用失败:', apiError)
      ElMessage.error('分析失败，未获取到真实数据')
      return
    }
    
    // 等待DOM更新后渲染图表
    nextTick(() => {
      renderSeasonalChart()
    })
  } catch (error) {
    console.error('分析失败:', error)
    // 错误已在接口分支提示，这里保留上次有效结果
  } finally {
    loading.value = false
  }
}

const SEASON_ORDER = [
  { key: 'Spring', label: '春季' },
  { key: 'Summer', label: '夏季' },
  { key: 'Autumn', label: '秋季' },
  { key: 'Winter', label: '冬季' }
]

const getSeasonSeries = () => {
  const seasonalPattern = analysisResult.value.seasonal_pattern || {}
  return SEASON_ORDER.map(({ key, label }) => {
    const item = seasonalPattern[key] || {}
    const electricity = Number(item.electricity_kwh || 0)
    const hvac = Number(item.hvac_kwh || 0)
    const outdoorTemp = Number(item.outdoor_temp || 0)
    return {
      key,
      label,
      electricity,
      hvac,
      outdoorTemp,
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

const noDataOption = () => ({
  title: {
    text: '季节性能耗分析（暂无数据）',
    left: 'center'
  },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value' },
  series: [{ type: 'bar', data: [] }]
})

// 计算属性 - 数据概览
const springAvgEnergy = computed(() => {
  const season = getSeasonSeries().find(item => item.key === 'Spring')
  return season ? season.total.toFixed(2) : '--'
})

const summerAvgEnergy = computed(() => {
  const season = getSeasonSeries().find(item => item.key === 'Summer')
  return season ? season.total.toFixed(2) : '--'
})

const autumnAvgEnergy = computed(() => {
  const season = getSeasonSeries().find(item => item.key === 'Autumn')
  return season ? season.total.toFixed(2) : '--'
})

const winterAvgEnergy = computed(() => {
  const season = getSeasonSeries().find(item => item.key === 'Winter')
  return season ? season.total.toFixed(2) : '--'
})

const annualTotalEnergy = computed(() => {
  const series = getSeasonSeries()
  const total = series.reduce((sum, item) => sum + item.total, 0)
  return total > 0 ? Math.round(total) : '--'
})

const renderSeasonalChart = () => {
  if (!seasonalChart.value) return
  
  if (charts.value.seasonal) {
    charts.value.seasonal.dispose()
  }
  
  charts.value.seasonal = echarts.init(seasonalChart.value)
  const seasonSeries = getSeasonSeries()
  const hasData = seasonSeries.some(item => item.total > 0)
  if (!hasData) {
    safeSetOption(charts.value.seasonal, noDataOption(), '季节性能耗图')
    return
  }

  const seasons = seasonSeries.map(item => item.label)
  const electricityData = seasonSeries.map(item => item.electricity)
  const hvacData = seasonSeries.map(item => item.hvac)
  const totalData = seasonSeries.map(item => item.total)
  const energyChangeRate = totalData.map((value, index) => {
    if (index === 0 || totalData[index - 1] === 0) return 0
    return Number((((value - totalData[index - 1]) / totalData[index - 1]) * 100).toFixed(1))
  })
  
  const option = {
    title: {
      text: '季节性能耗分析',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['电力消耗', 'HVAC能耗', '总能耗', '能耗变化率'],
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
      data: seasons,
      name: '季节'
    },
    yAxis: [
      {
        type: 'value',
        name: '能耗(kWh)',
        position: 'left',
        scale: true, // 启用自动缩放
        axisLabel: {
          formatter: '{value} kWh'
        }
      },
      {
        type: 'value',
        name: '变化率(%)',
        position: 'right',
        scale: true, // 启用自动缩放
        axisLabel: {
          formatter: '{value}%'
        }
      }
    ],
    series: [
      {
        name: '电力消耗',
        type: 'line',
        smooth: true,
        data: electricityData,
        itemStyle: {
          color: '#ff7f50'
        },
        lineStyle: {
          width: 3
        },
        symbol: 'circle',
        symbolSize: 8
      },
      {
        name: 'HVAC能耗',
        type: 'line',
        smooth: true,
        data: hvacData,
        itemStyle: {
          color: '#4682b4'
        },
        lineStyle: {
          width: 3
        },
        symbol: 'circle',
        symbolSize: 8
      },
      {
        name: '总能耗',
        type: 'bar',
        data: totalData,
        itemStyle: {
          color: function(params) {
            // 根据季节设置不同颜色
            const colors = ['#98d8c8', '#f7dc6f', '#bb8fce', '#85c1e9']
            return colors[params.dataIndex]
          }
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      },
      {
        name: '能耗变化率',
        type: 'line',
        yAxisIndex: 1,
        data: energyChangeRate,
        itemStyle: {
          color: function(params) {
            return parseFloat(params.value) >= 0 ? '#52c41a' : '#ff4d4f'
          }
        },
        lineStyle: {
          width: 3,
          type: 'dashed'
        },
        symbol: 'triangle',
        symbolSize: 10,
        markLine: {
          data: [
            {
              yAxis: 0,
              name: '基准线'
            }
          ]
        }
      }
    ]
  }
  
  safeSetOption(charts.value.seasonal, option, '季节性能耗图')
}

// 数据导出
const exportData = (format) => {
  const exportData = getSeasonSeries().filter(item => item.total > 0)
  if (exportData.length === 0) {
    ElMessage.warning('当前无可导出的真实数据')
    return
  }
  
  // 生成CSV内容
  let csvContent = '季节,电力消耗(kWh),HVAC能耗(kWh),总能耗(kWh)\n'
  exportData.forEach(item => {
    csvContent += `${item.label},${item.electricity.toFixed(2)},${item.hvac.toFixed(2)},${item.total.toFixed(2)}\n`
  })
  
  // 创建下载链接
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `季节性分析_${new Date().toISOString().split('T')[0]}.${format}`)
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
  setTimeRange()
})
</script>

<style scoped>
.seasonal-pattern-chart-page {
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

.chart-container {
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.chart {
  width: 100%;
  height: 500px;
}

.export-section {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

/* 响应式设计 */
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
    height: 400px;
  }
}
</style>