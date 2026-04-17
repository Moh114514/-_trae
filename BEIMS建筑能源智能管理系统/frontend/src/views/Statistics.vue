<template>
  <div class="statistics">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>统计分析</span>
        </div>
      </template>
      
      <el-form :model="statForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="建筑ID">
              <el-select
                v-model="statForm.building_id"
                placeholder="请选择建筑"
                clearable
                filterable
              >
                <el-option
                  v-for="building in buildings"
                  :key="building.building_id"
                  :label="building.building_id"
                  :value="building.building_id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="时间周期">
              <el-select v-model="statForm.period" placeholder="请选择周期">
                <el-option label="小时" value="hour" />
                <el-option label="天" value="day" />
                <el-option label="周" value="week" />
                <el-option label="月" value="month" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始时间">
              <el-date-picker
                v-model="statForm.start_time"
                type="datetime"
                placeholder="选择开始时间"
                format="YYYY-MM-DD HH:mm:ss"
                value-format="YYYY-MM-DD HH:mm:ss"
              />
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="结束时间">
              <el-date-picker
                v-model="statForm.end_time"
                type="datetime"
                placeholder="选择结束时间"
                format="YYYY-MM-DD HH:mm:ss"
                value-format="YYYY-MM-DD HH:mm:ss"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleAnalyze">
            <el-icon><DataAnalysis /></el-icon>
            开始分析
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 综合可视化图表区域 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>分析结果</span>
        </div>
      </template>
      
      <!-- 能耗汇总 -->
      <el-descriptions title="能耗汇总" :column="2" border style="margin-bottom: 20px;">
        <el-descriptions-item label="总电力消耗(kWh)">
          {{ formatFixed(analysisResult.summary?.total_electricity_kwh) }}
        </el-descriptions-item>
        <el-descriptions-item label="总用水量(m³)">
          {{ formatFixed(analysisResult.summary?.total_water_m3) }}
        </el-descriptions-item>
        <el-descriptions-item label="总HVAC能耗(kWh)">
          {{ formatFixed(analysisResult.summary?.total_hvac_kwh) }}
        </el-descriptions-item>
        <el-descriptions-item label="平均室外温度(°C)">
          {{ formatFixed(analysisResult.summary?.avg_outdoor_temp) }}
        </el-descriptions-item>
      </el-descriptions>
      
      <!-- 能耗趋势图表 -->
      <el-card shadow="hover" class="mb-4">
        <template #header>
          <span>能耗趋势</span>
        </template>
        <div ref="trendChart" style="width: 100%; height: 400px;"></div>
      </el-card>
      
      <!-- 峰值需求和能耗强度分析 -->
      <el-row :gutter="20" class="mb-4">
        <el-col :span="12">
          <el-card shadow="hover">
            <template #header>
              <span>峰值需求分析</span>
            </template>
            <div ref="peakDemandChart" style="width: 100%; height: 300px;"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="hover">
            <template #header>
              <span>能耗强度分析</span>
            </template>
            <div ref="intensityChart" style="width: 100%; height: 300px;"></div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 对比分析和天气相关性 -->
      <el-row :gutter="20" class="mb-4">
        <el-col :span="12">
          <el-card shadow="hover">
            <template #header>
              <span>对比分析</span>
            </template>
            <div ref="comparisonChart" style="width: 100%; height: 300px;"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="hover">
            <template #header>
              <span>天气相关性分析</span>
            </template>
            <div ref="weatherCorrelationChart" style="width: 100%; height: 300px;"></div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 人员影响和小时模式分析 -->
      <el-row :gutter="20" class="mb-4">
        <el-col :span="12">
          <el-card shadow="hover">
            <template #header>
              <span>人员影响分析</span>
            </template>
            <div ref="occupancyImpactChart" style="width: 100%; height: 300px;"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="hover">
            <template #header>
              <span>小时模式分析</span>
            </template>
            <div ref="hourlyPatternChart" style="width: 100%; height: 300px;"></div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 周模式和季节性分析 -->
      <el-row :gutter="20" class="mb-4">
        <el-col :span="12">
          <el-card shadow="hover">
            <template #header>
              <span>周模式分析</span>
            </template>
            <div ref="weeklyPatternChart" style="width: 100%; height: 300px;"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="hover">
            <template #header>
              <span>季节性分析</span>
            </template>
            <div ref="seasonalChart" style="width: 100%; height: 300px;"></div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 异常检测 -->
      <el-card shadow="hover" class="mb-4">
        <template #header>
          <span>异常检测</span>
        </template>
        <el-alert
          :title="`检测到 ${analysisResult.total_anomalies || 0} 个异常`"
          type="warning"
          :closable="false"
          style="margin-bottom: 20px;"
        />
        <el-table :data="analysisResult.anomalies || []" stripe border max-height="400">
          <el-table-column prop="timestamp" label="时间" width="180" />
          <el-table-column prop="metric" label="指标" width="150" />
          <el-table-column prop="value" label="数值" width="120">
            <template #default="{ row }">
              {{ formatMetricValue(row.value) }}
            </template>
          </el-table-column>
          <el-table-column prop="z_score" label="Z分数" width="120">
            <template #default="{ row }">
              {{ formatFixed(row.z_score) }}
            </template>
          </el-table-column>
          <el-table-column prop="type" label="类型" />
        </el-table>
      </el-card>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useAppStore } from '@/store'
import { dataAPI, queryAPI } from '@/api'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const appStore = useAppStore()

const buildings = ref([])
const loading = ref(false)
const analysisResult = ref({
  summary: {
    total_electricity_kwh: 0,
    total_water_m3: 0,
    total_hvac_kwh: 0,
    avg_outdoor_temp: 0,
    avg_humidity: 0
  },
  daily_data: [],
  rolling_mean: [],
  hourly_profile: {},
  peak_hour: 12,
  peak_hour_avg_consumption: 0,
  daily_peak_data: [],
  daily_intensity_kwh_per_sqm: [],
  average_intensity: 0,
  occupancy_correlation: 0,
  comparison_data: {},
  building_count: 0,
  correlations: {
    electricity_vs_temp: 0,
    electricity_vs_humidity: 0,
    hvac_vs_temp: 0,
    hvac_vs_humidity: 0
  },
  raw_data: [],
  correlation: 0,
  occupancy_impact: {},
  hourly_pattern: {},
  weekly_pattern: {},
  seasonal_pattern: {},
  total_anomalies: 0,
  anomalies: []
})
const charts = ref({})

// 图表容器 ref
const trendChart = ref(null)
const peakDemandChart = ref(null)
const intensityChart = ref(null)
const comparisonChart = ref(null)
const weatherCorrelationChart = ref(null)
const occupancyImpactChart = ref(null)
const hourlyPatternChart = ref(null)
const weeklyPatternChart = ref(null)
const seasonalChart = ref(null)

// 设置默认时间范围为包含数据库中数据的时间范围
// 数据库中的数据从2021-01-01开始
const startDate = new Date('2021-01-01')
const endDate = new Date('2021-01-31')

const formatDate = (date) => {
  return date.toISOString().slice(0, 19).replace('T', ' ')
}

const formatFixed = (value, digits = 2) => {
  const num = Number(value)
  return Number.isFinite(num) ? num.toFixed(digits) : '--'
}

const formatMetricValue = (value) => {
  const num = Number(value)
  if (Number.isFinite(num)) {
    return num.toFixed(2)
  }
  return value ?? '--'
}

const statForm = ref({
  building_id: '',
  period: 'day',
  start_time: formatDate(startDate),
  end_time: formatDate(endDate)
})

const loadBuildings = async () => {
  try {
    console.log('开始加载建筑列表...')
    const res = await dataAPI.getBuildings()
    console.log('获取建筑列表成功:', res.data)
    buildings.value = res.data.buildings
    appStore.setBuildings(res.data.buildings)
    
    // 如果有建筑数据，自动选择第一个建筑作为默认值
    if (buildings.value.length > 0) {
      statForm.value.building_id = buildings.value[0].building_id
      console.log('自动选择建筑:', buildings.value[0].building_id)
    } else {
      console.log('没有建筑数据，手动设置默认建筑ID')
      // 如果没有建筑数据，手动设置一个默认的建筑ID
      statForm.value.building_id = 'Aral'
    }
  } catch (error) {
    console.error('加载建筑列表失败:', error)
    console.error('错误响应:', error.response)
    // 如果加载失败，手动设置一个默认的建筑ID
    console.log('加载建筑列表失败，手动设置默认建筑ID')
    statForm.value.building_id = 'Aral'
  }
}

const handleAnalyze = async () => {
  loading.value = true
  // 保持 analysisResult 的初始值，不要设置为空对象
  
  try {
    // 验证必要参数
    if (!statForm.value.building_id) {
      ElMessage.warning('请选择建筑ID')
      loading.value = false
      return
    }
    
    if (!statForm.value.start_time || !statForm.value.end_time) {
      ElMessage.warning('请选择开始时间和结束时间')
      loading.value = false
      return
    }
    
    const params = {
      building_id: statForm.value.building_id,
      period: statForm.value.period,
      start_time: statForm.value.start_time,
      end_time: statForm.value.end_time
    }
    const rawQueryParams = {
      building_id: statForm.value.building_id,
      start_time: statForm.value.start_time,
      end_time: statForm.value.end_time,
      page: 1,
      page_size: 100000
    }
    
    console.log('API请求参数:', params)
    
    // 并行获取所有分析数据
    try {
      // 对比分析需要多个建筑ID，使用所有可用的建筑ID
      let buildingIds = buildings.value.map(b => b.building_id)
      // 如果没有建筑数据，手动设置一些默认的建筑ID
      if (buildingIds.length === 0) {
        buildingIds = ['Aral', 'Baikal', 'Caspian', 'Erie', 'Huron', 'Ladoga', 'Malawi', 'Michigan', 'Ontario', 'Superior', 'Titicaca', 'Victoria', 'Vostok', 'Winnipeg']
      }
      const comparisonParams = { ...params, building_ids: buildingIds }
      
      console.log('开始调用API...')
      
      // 并行调用所有API，处理每个API可能的失败
      const [
        timeAggregationRes,
        trendRes,
        peakDemandRes,
        intensityRes,
        comparisonRes,
        weatherCorrelationRes,
        occupancyImpactRes,
        hourlyPatternRes,
        weeklyPatternRes,
        seasonalRes,
        anomaliesRes,
        rawDataRes
      ] = await Promise.all([
        queryAPI.timeAggregation(params).catch(err => {
          console.error('timeAggregation API 调用失败:', err)
          return { data: { summary: { total_electricity_kwh: 0, total_water_m3: 0, total_hvac_kwh: 0, avg_outdoor_temp: 0, avg_humidity: 0 } } }
        }),
        queryAPI.getTrend(params).catch(err => {
          console.error('getTrend API 调用失败:', err)
          return { data: { daily_data: [], rolling_mean: [] } }
        }),
        queryAPI.getPeakDemand(params).catch(err => {
          console.error('getPeakDemand API 调用失败:', err)
          return { data: { hourly_profile: {}, peak_hour: 12, peak_hour_avg_consumption: 0, daily_peak_data: [] } }
        }),
        queryAPI.getIntensity(params).catch(err => {
          console.error('getIntensity API 调用失败:', err)
          return { data: { daily_intensity_kwh_per_sqm: [], average_intensity: 0, occupancy_correlation: 0 } }
        }),
        queryAPI.getComparison(comparisonParams).catch(err => {
          console.error('getComparison API 调用失败:', err)
          return { data: { comparison_data: {}, building_count: 0 } }
        }),
        queryAPI.getWeatherCorrelation(params).catch(err => {
          console.error('getWeatherCorrelation API 调用失败:', err)
          return { data: { correlations: { electricity_vs_temp: 0, electricity_vs_humidity: 0, hvac_vs_temp: 0, hvac_vs_humidity: 0 } } }
        }),
        queryAPI.getOccupancyImpact(params).catch(err => {
          console.error('getOccupancyImpact API 调用失败:', err)
          return { data: { correlation: 0, occupancy_impact: {} } }
        }),
        queryAPI.getHourlyPattern(params).catch(err => {
          console.error('getHourlyPattern API 调用失败:', err)
          return { data: { hourly_pattern: {} } }
        }),
        queryAPI.getWeeklyPattern(params).catch(err => {
          console.error('getWeeklyPattern API 调用失败:', err)
          return { data: { weekly_pattern: {} } }
        }),
        queryAPI.getSeasonal(params).catch(err => {
          console.error('getSeasonal API 调用失败:', err)
          return { data: { seasonal_pattern: {} } }
        }),
        queryAPI.detectAnomalies(params).catch(err => {
          console.error('detectAnomalies API 调用失败:', err)
          return { data: { total_anomalies: 0, anomalies: [] } }
        }),
        queryAPI.queryData(rawQueryParams).catch(err => {
          console.error('queryData API 调用失败:', err)
          return { data: { data: [] } }
        })
      ])
      
      console.log('API调用完成，开始处理响应...')
      console.log('timeAggregationRes:', timeAggregationRes)
      console.log('trendRes:', trendRes)
      console.log('peakDemandRes:', peakDemandRes)
      console.log('intensityRes:', intensityRes)
      console.log('comparisonRes:', comparisonRes)
      console.log('weatherCorrelationRes:', weatherCorrelationRes)
      console.log('occupancyImpactRes:', occupancyImpactRes)
      console.log('hourlyPatternRes:', hourlyPatternRes)
      console.log('weeklyPatternRes:', weeklyPatternRes)
      console.log('seasonalRes:', seasonalRes)
      console.log('anomaliesRes:', anomaliesRes)
      console.log('rawDataRes:', rawDataRes)
      
      // 检查每个API返回的数据是否包含错误信息，如果包含，则使用默认值
      const timeAggregationData = timeAggregationRes.data.error ? { summary: { total_electricity_kwh: 0, total_water_m3: 0, total_hvac_kwh: 0, avg_outdoor_temp: 0, avg_humidity: 0 } } : timeAggregationRes.data;
      const trendData = trendRes.data.error ? { daily_data: [], rolling_mean: [] } : trendRes.data;
      const peakDemandData = peakDemandRes.data.error ? { hourly_profile: {}, peak_hour: 12, peak_hour_avg_consumption: 0, daily_peak_data: [] } : peakDemandRes.data;
      const intensityData = intensityRes.data.error ? { daily_intensity_kwh_per_sqm: [], average_intensity: 0, occupancy_correlation: 0 } : intensityRes.data;
      const comparisonData = comparisonRes.data.error ? { comparison_data: {}, building_count: 0 } : comparisonRes.data;
      const weatherCorrelationData = weatherCorrelationRes.data.error ? { correlations: { electricity_vs_temp: 0, electricity_vs_humidity: 0, hvac_vs_temp: 0, hvac_vs_humidity: 0 } } : weatherCorrelationRes.data;
      const occupancyImpactData = occupancyImpactRes.data.error ? { correlation: 0, occupancy_impact: {} } : occupancyImpactRes.data;
      const hourlyPatternData = hourlyPatternRes.data.error ? { hourly_pattern: {} } : hourlyPatternRes.data;
      const weeklyPatternData = weeklyPatternRes.data.error ? { weekly_pattern: {} } : weeklyPatternRes.data;
      const seasonalData = seasonalRes.data.error ? { seasonal_pattern: {} } : seasonalRes.data;
      const anomaliesData = anomaliesRes.data.error ? { total_anomalies: 0, anomalies: [] } : anomaliesRes.data;
      const rawData = Array.isArray(rawDataRes.data?.data) ? rawDataRes.data.data : [];
      
      // 合并所有分析结果，确保所有数据对象都是有效的对象
      analysisResult.value = {
        ...(timeAggregationData || {}),
        ...(trendData || {}),
        ...(peakDemandData || {}),
        ...(intensityData || {}),
        ...(comparisonData || {}),
        ...(weatherCorrelationData || {}),
        ...(occupancyImpactData || {}),
        ...(hourlyPatternData || {}),
        ...(weeklyPatternData || {}),
        ...(seasonalData || {}),
        ...(anomaliesData || {}),
        raw_data: rawData
      }
      
      // 确保所有必要的字段都存在
      if (!analysisResult.value.summary) {
        analysisResult.value.summary = {
          total_electricity_kwh: 0,
          total_water_m3: 0,
          total_hvac_kwh: 0,
          avg_outdoor_temp: 0,
          avg_humidity: 0
        }
      }
      
      if (!analysisResult.value.daily_data) {
        analysisResult.value.daily_data = []
      }
      
      if (!analysisResult.value.rolling_mean) {
        analysisResult.value.rolling_mean = []
      }
      
      if (!analysisResult.value.hourly_profile) {
        analysisResult.value.hourly_profile = {}
      }
      
      if (!analysisResult.value.daily_intensity_kwh_per_sqm) {
        analysisResult.value.daily_intensity_kwh_per_sqm = []
      }
      
      if (!analysisResult.value.comparison_data) {
        analysisResult.value.comparison_data = {}
      }
      
      if (!analysisResult.value.correlations) {
        analysisResult.value.correlations = {
          electricity_vs_temp: 0,
          electricity_vs_humidity: 0,
          hvac_vs_temp: 0,
          hvac_vs_humidity: 0
        }
      }
      
      if (!analysisResult.value.correlation) {
        analysisResult.value.correlation = 0
      }

      if (!analysisResult.value.raw_data) {
        analysisResult.value.raw_data = []
      }
      
      if (!analysisResult.value.occupancy_impact) {
        analysisResult.value.occupancy_impact = {}
      }
      
      if (!analysisResult.value.hourly_pattern) {
        analysisResult.value.hourly_pattern = {}
      }
      
      if (!analysisResult.value.weekly_pattern) {
        analysisResult.value.weekly_pattern = {}
      }
      
      if (!analysisResult.value.seasonal_pattern) {
        analysisResult.value.seasonal_pattern = {}
      }
      
      if (!analysisResult.value.total_anomalies) {
        analysisResult.value.total_anomalies = 0
      }
      
      if (!analysisResult.value.anomalies) {
        analysisResult.value.anomalies = []
      }
      
      console.log('分析结果:', JSON.stringify(analysisResult.value, null, 2))
      ElMessage.success('分析完成')
      
      // 等待DOM更新后渲染图表
      nextTick(() => {
        renderCharts()
      })
    } catch (apiError) {
      console.error('API调用失败:', apiError)
      console.error('错误响应:', apiError.response)
      throw apiError
    }
  } catch (error) {
    console.error('分析失败:', error)
    if (error.response && error.response.status === 500) {
      ElMessage.error('服务器内部错误，请稍后重试')
    } else if (error.response && error.response.status === 400) {
      ElMessage.error('请求参数错误，请检查输入')
    } else if (error.response && error.response.status === 404) {
      ElMessage.error('请求的资源不存在')
    } else {
      ElMessage.error('分析失败，请检查网络连接或联系管理员')
    }
  } finally {
    loading.value = false
  }
}

const renderCharts = () => {
  // 渲染所有图表
  renderTrendChart()
  renderPeakDemandChart()
  renderIntensityChart()
  renderComparisonChart()
  renderWeatherCorrelationChart()
  renderOccupancyImpactChart()
  renderHourlyPatternChart()
  renderWeeklyPatternChart()
  renderSeasonalChart()
}

const renderTrendChart = () => {
  if (!trendChart.value) return
  
  if (charts.value.trend) {
    charts.value.trend.dispose()
  }
  
  charts.value.trend = echarts.init(trendChart.value)
  
  const dailyData = analysisResult.value.daily_data || analysisResult.value.data || []
  const xAxisData = dailyData.map(item => item.timestamp)
  const electricityData = dailyData.map(item => item.electricity_kwh)
  
  const option = {
    title: {
      text: '能耗趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['电力消耗(kWh)', '7天移动平均'],
      bottom: 0
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
      name: '能耗(kWh)'
    },
    series: [
      {
        name: '电力消耗(kWh)',
        type: 'line',
        data: electricityData,
        smooth: true
      },
      {
        name: '7天移动平均',
        type: 'line',
        data: analysisResult.value.rolling_mean?.map(item => item.electricity_kwh) || [],
        smooth: true,
        itemStyle: {
          color: '#ff7f50'
        }
      }
    ]
  }
  
  charts.value.trend.setOption(option)
}

const renderPeakDemandChart = () => {
  if (!peakDemandChart.value) return
  
  if (charts.value.peakDemand) {
    charts.value.peakDemand.dispose()
  }
  
  charts.value.peakDemand = echarts.init(peakDemandChart.value)
  
  const hourlyProfile = analysisResult.value.hourly_profile || {}
  const xAxisData = Object.keys(hourlyProfile).sort((a, b) => parseInt(a) - parseInt(b))
  const peakData = xAxisData.map(hour => hourlyProfile[hour])
  
  const option = {
    title: {
      text: '峰值需求分析',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      name: '小时'
    },
    yAxis: {
      type: 'value',
      name: '平均电力消耗(kWh)'
    },
    series: [
      {
        name: '小时平均消耗',
        type: 'bar',
        data: peakData,
        itemStyle: {
          color: '#ff7f50'
        }
      }
    ]
  }
  
  charts.value.peakDemand.setOption(option)
}

const renderIntensityChart = () => {
  if (!intensityChart.value) return
  
  if (charts.value.intensity) {
    charts.value.intensity.dispose()
  }
  
  charts.value.intensity = echarts.init(intensityChart.value)
  
  const dailyIntensity = analysisResult.value.daily_intensity_kwh_per_sqm || []
  const xAxisData = dailyIntensity.map(item => item.date)
  const intensityData = dailyIntensity.map(item => item.intensity)
  
  const option = {
    title: {
      text: '能耗强度分析',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
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
        }
      }
    ]
  }
  
  charts.value.intensity.setOption(option)
}

const renderComparisonChart = () => {
  if (!comparisonChart.value) return
  
  if (charts.value.comparison) {
    charts.value.comparison.dispose()
  }
  
  charts.value.comparison = echarts.init(comparisonChart.value)
  
  const comparisonData = analysisResult.value.comparison_data || {}
  const xAxisData = Object.keys(comparisonData)
  const electricityData = xAxisData.map(building => comparisonData[building].total_electricity)
  const hvacData = xAxisData.map(building => comparisonData[building].total_hvac)
  const waterData = xAxisData.map(building => comparisonData[building].total_water)
  
  const option = {
    title: {
      text: '对比分析',
      left: 'center'
    },
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
        data: electricityData
      },
      {
        name: 'HVAC能耗(kWh)',
        type: 'bar',
        data: hvacData
      },
      {
        name: '用水量(m³)',
        type: 'bar',
        data: waterData
      }
    ]
  }
  
  charts.value.comparison.setOption(option)
}

const renderWeatherCorrelationChart = () => {
  if (!weatherCorrelationChart.value) return
  
  if (charts.value.weatherCorrelation) {
    charts.value.weatherCorrelation.dispose()
  }
  
  charts.value.weatherCorrelation = echarts.init(weatherCorrelationChart.value)
  
  const rawData = analysisResult.value.raw_data || []
  const scatterData = rawData
    .map(item => [Number(item.outdoor_temp), Number(item.electricity_kwh)])
    .filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y))
  
  const option = {
    title: {
      text: '天气相关性分析',
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        const x = Number(params.value?.[0])
        const y = Number(params.value?.[1])
        return `温度: ${Number.isFinite(x) ? x.toFixed(1) : '--'}°C<br/>电力消耗: ${Number.isFinite(y) ? y.toFixed(2) : '--'}kWh`
      }
    },
    xAxis: {
      type: 'value',
      name: '室外温度(°C)'
    },
    yAxis: {
      type: 'value',
      name: '电力消耗(kWh)'
    },
    series: [
      {
        name: '相关性',
        type: 'scatter',
        data: scatterData,
        symbolSize: 8,
        itemStyle: {
          color: '#ff6347'
        }
      }
    ]
  }
  
  charts.value.weatherCorrelation.setOption(option)
}

const renderOccupancyImpactChart = () => {
  if (!occupancyImpactChart.value) return
  
  if (charts.value.occupancyImpact) {
    charts.value.occupancyImpact.dispose()
  }
  
  charts.value.occupancyImpact = echarts.init(occupancyImpactChart.value)
  
  const rawData = analysisResult.value.raw_data || []
  const scatterData = rawData
    .map(item => [Number(item.occupancy_density), Number(item.electricity_kwh)])
    .filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y))
  
  const option = {
    title: {
      text: '人员影响分析',
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        const x = Number(params.value?.[0])
        const y = Number(params.value?.[1])
        return `人员密度: ${Number.isFinite(x) ? x.toFixed(2) : '--'}<br/>电力消耗: ${Number.isFinite(y) ? y.toFixed(2) : '--'}kWh`
      }
    },
    xAxis: {
      type: 'value',
      name: '人员密度'
    },
    yAxis: {
      type: 'value',
      name: '电力消耗(kWh)'
    },
    series: [
      {
        name: '人员影响',
        type: 'scatter',
        data: scatterData,
        symbolSize: 8,
        itemStyle: {
          color: '#4682b4'
        }
      }
    ]
  }
  
  charts.value.occupancyImpact.setOption(option)
}

const renderHourlyPatternChart = () => {
  if (!hourlyPatternChart.value) return
  
  if (charts.value.hourlyPattern) {
    charts.value.hourlyPattern.dispose()
  }
  
  charts.value.hourlyPattern = echarts.init(hourlyPatternChart.value)
  
  const hourlyPattern = analysisResult.value.hourly_pattern || {}
  const xAxisData = Object.keys(hourlyPattern).sort((a, b) => parseInt(a) - parseInt(b))
  const electricityData = xAxisData.map(hour => hourlyPattern[hour]?.electricity_kwh || 0)
  const hvacData = xAxisData.map(hour => hourlyPattern[hour]?.hvac_kwh || 0)
  
  const option = {
    title: {
      text: '小时模式分析',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['电力消耗(kWh)', 'HVAC能耗(kWh)'],
      bottom: 0
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      name: '小时'
    },
    yAxis: {
      type: 'value',
      name: '能耗'
    },
    series: [
      {
        name: '电力消耗(kWh)',
        type: 'line',
        data: electricityData,
        smooth: true
      },
      {
        name: 'HVAC能耗(kWh)',
        type: 'line',
        data: hvacData,
        smooth: true
      }
    ]
  }
  
  charts.value.hourlyPattern.setOption(option)
}

const renderWeeklyPatternChart = () => {
  if (!weeklyPatternChart.value) return
  
  if (charts.value.weeklyPattern) {
    charts.value.weeklyPattern.dispose()
  }
  
  charts.value.weeklyPattern = echarts.init(weeklyPatternChart.value)
  
  const weeklyPattern = analysisResult.value.weekly_pattern || {}
  const xAxisData = Object.keys(weeklyPattern)
  const electricityData = xAxisData.map(day => weeklyPattern[day]?.electricity_kwh || 0)
  const hvacData = xAxisData.map(day => weeklyPattern[day]?.hvac_kwh || 0)
  
  const option = {
    title: {
      text: '周模式分析',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['电力消耗(kWh)', 'HVAC能耗(kWh)'],
      bottom: 0
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      name: '星期'
    },
    yAxis: {
      type: 'value',
      name: '能耗'
    },
    series: [
      {
        name: '电力消耗(kWh)',
        type: 'bar',
        data: electricityData
      },
      {
        name: 'HVAC能耗(kWh)',
        type: 'bar',
        data: hvacData
      }
    ]
  }
  
  charts.value.weeklyPattern.setOption(option)
}

const renderSeasonalChart = () => {
  if (!seasonalChart.value) return
  
  if (charts.value.seasonal) {
    charts.value.seasonal.dispose()
  }
  
  charts.value.seasonal = echarts.init(seasonalChart.value)
  
  const seasonalPattern = analysisResult.value.seasonal_pattern || {}
  const xAxisData = Object.keys(seasonalPattern)
  const electricityData = xAxisData.map(season => seasonalPattern[season]?.electricity_kwh || 0)
  const hvacData = xAxisData.map(season => seasonalPattern[season]?.hvac_kwh || 0)
  
  const option = {
    title: {
      text: '季节性分析',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['电力消耗(kWh)', 'HVAC能耗(kWh)'],
      bottom: 0
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      name: '季节'
    },
    yAxis: {
      type: 'value',
      name: '能耗'
    },
    series: [
      {
        name: '电力消耗(kWh)',
        type: 'line',
        data: electricityData,
        smooth: true
      },
      {
        name: 'HVAC能耗(kWh)',
        type: 'line',
        data: hvacData,
        smooth: true
      }
    ]
  }
  
  charts.value.seasonal.setOption(option)
}

onMounted(() => {
  loadBuildings()
})

// 注释掉自动分析的 watcher，只有点击开始分析按钮时才进行分析
// watch(() => statForm.value.building_id, (newBuildingId) => {
//   if (newBuildingId) {
//     handleAnalyze()
//   }
// })

// 监听窗口大小变化，调整图表大小
window.addEventListener('resize', () => {
  Object.values(charts.value).forEach(chart => {
    chart?.resize()
  })
})
</script>

<style scoped>
.statistics {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

pre {
  background-color: #f5f7fa;
  padding: 20px;
  border-radius: 4px;
  overflow-x: auto;
}

.mb-4 {
  margin-bottom: 16px;
}
</style>
