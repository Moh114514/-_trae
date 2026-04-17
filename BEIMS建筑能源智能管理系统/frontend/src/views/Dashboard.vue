<template>
  <div class="dashboard-screen">
    <!-- 3D模型作为全屏背景 -->
    <div class="building-simulation-fullscreen">
      <Building3DModel />
    </div>

    <!-- 头部区域 -->
    <div class="dashboard-header">
      <div class="header-left">
        <div class="current-time">{{ currentTime }}</div>
        <div class="current-date">{{ currentDate }}</div>
      </div>
      <div class="header-center">
        <h1 class="system-title">建筑能源智能管理系统 BEIMS</h1>
        <p class="system-subtitle">Building Energy Intelligent Management System</p>
      </div>
      <div class="header-right">
        <div class="weather-info">
          <el-icon><PartlyCloudy /></el-icon>
          <span>{{ weather.temp }}°C</span>
          <span class="weather-desc">{{ weather.desc }}</span>
        </div>
        <el-dropdown trigger="click" class="nav-dropdown">
          <el-button type="primary" class="nav-btn">
            <el-icon><Menu /></el-icon>
            <span>功能菜单</span>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="goTo('/dashboard')">
                <el-icon><Odometer /></el-icon>
                综合概览
              </el-dropdown-item>
              <el-dropdown-item divided @click="goTo('/data-import')">
                <el-icon><Upload /></el-icon>
                数据导入
              </el-dropdown-item>
              <el-dropdown-item @click="goTo('/query')">
                <el-icon><Search /></el-icon>
                数据查询
              </el-dropdown-item>
              <el-dropdown-item divided @click="goTo('/statistics/trend')">
                <el-icon><TrendCharts /></el-icon>
                能耗趋势
              </el-dropdown-item>
              <el-dropdown-item @click="goTo('/statistics/peak-demand')">
                <el-icon><Top /></el-icon>
                峰值需求分析
              </el-dropdown-item>
              <el-dropdown-item @click="goTo('/statistics/intensity')">
                <el-icon><Histogram /></el-icon>
                能耗强度分析
              </el-dropdown-item>
              <el-dropdown-item @click="goTo('/statistics/comparison')">
                <el-icon><Operation /></el-icon>
                对比分析
              </el-dropdown-item>
              <el-dropdown-item @click="goTo('/statistics/weather-correlation')">
                <el-icon><Sunny /></el-icon>
                天气相关性分析
              </el-dropdown-item>
              <el-dropdown-item @click="goTo('/statistics/occupancy-impact')">
                <el-icon><User /></el-icon>
                人员影响分析
              </el-dropdown-item>
              <el-dropdown-item @click="goTo('/statistics/hourly-pattern')">
                <el-icon><Timer /></el-icon>
                小时模式分析
              </el-dropdown-item>
              <el-dropdown-item @click="goTo('/statistics/weekly-pattern')">
                <el-icon><Calendar /></el-icon>
                周模式分析
              </el-dropdown-item>
              <el-dropdown-item @click="goTo('/statistics/seasonal-pattern')">
                <span style="margin-right: 8px;">🍃</span>
                季节性分析
              </el-dropdown-item>
              <el-dropdown-item divided @click="goTo('/intelligence')">
                <el-icon><ChatDotRound /></el-icon>
                智能问答
              </el-dropdown-item>
              <el-dropdown-item @click="goTo('/knowledge')">
                <el-icon><Collection /></el-icon>
                知识库管理
              </el-dropdown-item>
              <el-dropdown-item divided @click="goTo('/report')">
                <el-icon><Document /></el-icon>
                报表导出
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 主内容区域 - 只有左右面板可以交互，中间全部控制3D模型 -->
    <div class="dashboard-content">
      <div class="left-panel">
        <div class="panel-section">
          <div class="section-title">
            <span class="title-icon"></span>
            能耗概览
          </div>
          <div class="energy-overview">
            <div class="energy-item">
              <div class="energy-icon electricity">
                <el-icon><Lightning /></el-icon>
              </div>
              <div class="energy-info">
                <div class="energy-value">{{ formatNumber(realtimeData.electricity) }}</div>
                <div class="energy-unit">kWh</div>
                <div class="energy-label">实时电力消耗</div>
              </div>
              <div class="energy-trend up">
                <el-icon><Top /></el-icon>
                <span>12.5%</span>
              </div>
            </div>
            <div class="energy-item">
              <div class="energy-icon water">
                <el-icon><Drizzling /></el-icon>
              </div>
              <div class="energy-info">
                <div class="energy-value">{{ formatNumber(realtimeData.water) }}</div>
                <div class="energy-unit">m³</div>
                <div class="energy-label">实时用水量</div>
              </div>
              <div class="energy-trend down">
                <el-icon><Bottom /></el-icon>
                <span>8.3%</span>
              </div>
            </div>
            <div class="energy-item">
              <div class="energy-icon hvac">
                <el-icon><Cpu /></el-icon>
              </div>
              <div class="energy-info">
                <div class="energy-value">{{ formatNumber(realtimeData.hvac) }}</div>
                <div class="energy-unit">kWh</div>
                <div class="energy-label">HVAC能耗</div>
              </div>
              <div class="energy-trend up">
                <el-icon><Top /></el-icon>
                <span>5.2%</span>
              </div>
            </div>
            <div class="energy-item">
              <div class="energy-icon cop">
                <el-icon><Odometer /></el-icon>
              </div>
              <div class="energy-info">
                <div class="energy-value">{{ realtimeData.cop }}</div>
                <div class="energy-unit"></div>
                <div class="energy-label">系统COP</div>
              </div>
              <div class="energy-trend stable">
                <el-icon><Minus /></el-icon>
                <span>稳定</span>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-section trend-section">
          <div class="section-title">
            <span class="title-icon"></span>
            能耗趋势
          </div>
          <div ref="trendChart" class="chart-box chart-box-trend"></div>
        </div>

        <div class="panel-section">
          <div class="section-title">
            <span class="title-icon"></span>
            能耗分布
          </div>
          <div ref="pieChart" class="chart-box"></div>
        </div>

        <div class="panel-section">
          <div class="section-title">
            <span class="title-icon"></span>
            环境参数
          </div>
          <div class="env-grid">
            <div class="env-item">
              <div class="env-label">室外温度</div>
              <div class="env-value">{{ environment.outdoorTemp }}°C</div>
            </div>
            <div class="env-item">
              <div class="env-label">室内温度</div>
              <div class="env-value">{{ environment.indoorTemp }}°C</div>
            </div>
            <div class="env-item">
              <div class="env-label">湿度</div>
              <div class="env-value">{{ environment.humidity }}%</div>
            </div>
            <div class="env-item">
              <div class="env-label">人员密度</div>
              <div class="env-value">{{ environment.occupancy }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="right-panel">
        <div class="panel-section ranking-section">
          <div class="section-title">
            <span class="title-icon"></span>
            建筑能耗排名 TOP 14
          </div>
          <div ref="rankingChart" class="chart-box-ranking"></div>
        </div>

        <div class="panel-section">
          <div class="section-title">
            <span class="title-icon"></span>
            系统状态
          </div>
          <div class="status-grid">
            <div class="status-item" :class="{ active: systemStatus.chiller }">
              <div class="status-icon">
                <el-icon><Cpu /></el-icon>
              </div>
              <div class="status-info">
                <div class="status-name">冷水机组</div>
                <div class="status-value">{{ systemStatus.chiller ? '运行中' : '停止' }}</div>
              </div>
            </div>
            <div class="status-item" :class="{ active: systemStatus.coolingTower }">
              <div class="status-icon">
                <el-icon><WindPower /></el-icon>
              </div>
              <div class="status-info">
                <div class="status-name">冷却塔</div>
                <div class="status-value">{{ systemStatus.coolingTower ? '运行中' : '停止' }}</div>
              </div>
            </div>
            <div class="status-item" :class="{ active: systemStatus.pump }">
              <div class="status-icon">
                <el-icon><Refresh /></el-icon>
              </div>
              <div class="status-info">
                <div class="status-name">水泵系统</div>
                <div class="status-value">{{ systemStatus.pump ? '运行中' : '停止' }}</div>
              </div>
            </div>
            <div class="status-item" :class="{ active: systemStatus.ahu }">
              <div class="status-icon">
                <el-icon><Fan /></el-icon>
              </div>
              <div class="status-info">
                <div class="status-name">空气处理机组</div>
                <div class="status-value">{{ systemStatus.ahu ? '运行中' : '停止' }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-section">
          <div class="section-title">
            <span class="title-icon"></span>
            告警信息
          </div>
          <div class="alarm-list">
            <div v-for="(alarm, index) in alarms" :key="index" class="alarm-item" :class="alarm.level">
              <div class="alarm-icon">
                <el-icon><WarningFilled /></el-icon>
              </div>
              <div class="alarm-content">
                <div class="alarm-title">{{ alarm.title }}</div>
                <div class="alarm-time">{{ alarm.time }}</div>
              </div>
            </div>
            <div v-if="alarms.length === 0" class="no-alarm">
              <el-icon><CircleCheckFilled /></el-icon>
              <span>系统运行正常</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Unity 动画效果容器 -->
    <UnityAnimation />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { dataAPI, queryAPI } from '@/api'
import Building3DModel from '@/components/Building3DModel.vue'
import UnityAnimation from '@/components/UnityAnimation.vue'

const router = useRouter()

const currentTime = ref('')
const currentDate = ref('')
const dataSummary = ref({})
const buildings = ref([])
const selectedBuilding = ref(null)
const hoverBuilding = ref(null)

const realtimeData = ref({
  electricity: 15420,
  water: 1250,
  hvac: 8500,
  cop: 4.2
})

const weather = ref({
  temp: 25,
  desc: '多云'
})

const systemStatus = ref({
  chiller: true,
  coolingTower: true,
  pump: true,
  ahu: true
})

const alarms = ref([
  { title: 'Aral建筑电力消耗异常', time: '10:30:25', level: 'warning' },
  { title: '冷水机组2号效率下降', time: '09:15:42', level: 'info' },
  { title: '冷却塔水温偏高', time: '08:45:10', level: 'error' }
])

const environment = ref({
  outdoorTemp: 28,
  indoorTemp: 24,
  humidity: 65,
  occupancy: 3.5
})

const trendChart = ref(null)
const pieChart = ref(null)
const rankingChart = ref(null)

let trendChartInstance = null
let pieChartInstance = null
let rankingChartInstance = null
let timeInterval = null

const totalEnergy = computed(() => {
  return buildings.value.reduce((sum, b) => sum + (b.total_electricity || 0), 0)
})

const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 1000000) {
    return (num / 1000000).toFixed(2) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toFixed(0)
}

const updateTime = () => {
  const now = new Date()
  // 综合概览页面使用2026年，其他时间信息与系统时间一致
  const dashboardDate = new Date(now)
  dashboardDate.setFullYear(2026)
  
  currentTime.value = now.toLocaleTimeString('zh-CN', { hour12: false })
  currentDate.value = dashboardDate.toLocaleDateString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit',
    weekday: 'long'
  })
}

const goTo = (path) => {
  router.push(path)
}

const getBuilding3DStyle = (index, building) => {
  const positions = [
    { top: '20%', left: '15%' },
    { top: '25%', left: '28%' },
    { top: '22%', left: '42%' },
    { top: '18%', left: '55%' },
    { top: '25%', left: '68%' },
    { top: '20%', left: '82%' },
    { top: '45%', left: '12%' },
    { top: '50%', left: '25%' },
    { top: '48%', left: '38%' },
    { top: '45%', left: '52%' },
    { top: '50%', left: '65%' },
    { top: '48%', left: '78%' },
    { top: '70%', left: '30%' },
    { top: '72%', left: '70%' }
  ]
  
  const pos = positions[index % positions.length]
  
  return {
    top: pos.top,
    left: pos.left,
    transform: 'translate(-50%, -50%)'
  }
}

const getBuildingHeight = (building) => {
  const minHeight = 40
  const maxHeight = 120
  const height = minHeight + (building.percentage / 100) * (maxHeight - minHeight) * 3
  return Math.min(height, maxHeight)
}

const getWindowCount = (building) => {
  const height = getBuildingHeight(building)
  return Math.floor(height / 15) * 2
}

const getFloorCount = (building) => {
  const baseFloors = 3
  const extraFloors = Math.min(Math.floor(building.percentage / 5), 8)
  return baseFloors + extraFloors
}

const getBuildingTypeClass = (building) => {
  const typeMap = {
    'Office': 'office',
    'Commercial': 'commercial',
    'Residential': 'residential',
    'Hotel': 'hotel',
    'Hospital': 'hospital'
  }
  return typeMap[building.building_type] || 'office'
}

const getBuildingX = (index) => {
  const positions = [
    { top: '20%', left: '15%' },
    { top: '25%', left: '28%' },
    { top: '22%', left: '42%' },
    { top: '18%', left: '55%' },
    { top: '25%', left: '68%' },
    { top: '20%', left: '82%' },
    { top: '45%', left: '12%' },
    { top: '50%', left: '25%' },
    { top: '48%', left: '38%' },
    { top: '45%', left: '52%' },
    { top: '50%', left: '65%' },
    { top: '48%', left: '78%' },
    { top: '70%', left: '30%' },
    { top: '72%', left: '70%' }
  ]
  const pos = positions[index % positions.length]
  return parseFloat(pos.left) / 100 * 1000
}

const getBuildingY = (index) => {
  const positions = [
    { top: '20%', left: '15%' },
    { top: '25%', left: '28%' },
    { top: '22%', left: '42%' },
    { top: '18%', left: '55%' },
    { top: '25%', left: '68%' },
    { top: '20%', left: '82%' },
    { top: '45%', left: '12%' },
    { top: '50%', left: '25%' },
    { top: '48%', left: '38%' },
    { top: '45%', left: '52%' },
    { top: '50%', left: '65%' },
    { top: '48%', left: '78%' },
    { top: '70%', left: '30%' },
    { top: '72%', left: '70%' }
  ]
  const pos = positions[index % positions.length]
  return parseFloat(pos.top) / 100 * 600
}

const selectBuilding = (building) => {
  selectedBuilding.value = building.building_id
}

const viewBuildingDetail = (building) => {
  router.push({
    path: '/query',
    query: { building_id: building.building_id }
  })
}

const loadData = async () => {
  try {
    const res = await dataAPI.getSummary()
    dataSummary.value = res.data
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

const loadBuildings = async () => {
  try {
    const [buildingsRes, rankingRes] = await Promise.all([
      dataAPI.getBuildings(),
      queryAPI.getRanking({ top_n: 14 })
    ])
    
    const rankingData = rankingRes.data.ranking || []
    const totalEnergy = rankingData.reduce((sum, b) => sum + (b.total_electricity_kwh || 0), 0)
    
    buildings.value = rankingData.map((b, index) => {
      const buildingInfo = buildingsRes.data.buildings.find(bi => bi.building_id === b.building_id)
      const percentage = totalEnergy > 0 ? ((b.total_electricity_kwh / totalEnergy) * 100).toFixed(1) : 0
      
      let energyLevel = 'low'
      if (percentage > 10) {
        energyLevel = 'high'
      } else if (percentage > 5) {
        energyLevel = 'medium'
      }
      
      return {
        building_id: b.building_id,
        building_type: buildingInfo?.building_type || 'Unknown',
        total_electricity: b.total_electricity_kwh,
        total_water: b.total_water_m3,
        total_hvac: b.total_hvac_kwh,
        percentage: percentage,
        energy_level: energyLevel
      }
    })
  } catch (error) {
    console.error('加载建筑数据失败:', error)
  }
}

const initCharts = async () => {
  const chartTheme = {
    backgroundColor: 'transparent',
    textStyle: { color: '#fff' }
  }

  trendChartInstance = echarts.init(trendChart.value)
  pieChartInstance = echarts.init(pieChart.value)
  rankingChartInstance = echarts.init(rankingChart.value)

  const rankingData = buildings.value.map(b => ({
    id: b.building_id,
    value: b.total_electricity
  })).sort((a, b) => a.value - b.value)
  
  rankingChartInstance.setOption({
    ...chartTheme,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(0,0,0,0.8)',
      borderColor: '#00d4ff',
      textStyle: { color: '#fff' },
      formatter: (params) => {
        const data = params[0]
        const building = buildings.value.find(b => b.building_id === data.name)
        return `
          <div style="padding: 10px;">
            <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px;">${data.name}</div>
            <div style="margin: 4px 0;">类型: ${building?.building_type || 'Unknown'}</div>
            <div style="margin: 4px 0;">能耗: ${formatNumber(data.value)} kWh</div>
            <div style="margin: 4px 0;">占比: ${building?.percentage}%</div>
          </div>
        `
      }
    },
    grid: {
      left: '20%',
      right: '15%',
      top: '5%',
      bottom: '10%'
    },
    xAxis: {
      type: 'value',
      name: 'kWh',
      nameTextStyle: { color: '#00d4ff' },
      axisLine: { lineStyle: { color: '#1e4d6b' } },
      axisLabel: { 
        color: '#8ec6e3', 
        interval: 2,
        formatter: (value) => {
          if (value >= 1000000) {
            return (value / 1000000).toFixed(1) + 'M'
          } else if (value >= 1000) {
            return (value / 1000).toFixed(1) + 'K'
          }
          return value
        }
      },
      splitLine: { lineStyle: { color: '#1e4d6b', type: 'dashed' }, interval: 2 }
    },
    yAxis: {
      type: 'category',
      data: rankingData.map(r => r.id),
      axisLine: { lineStyle: { color: '#1e4d6b' } },
      axisLabel: { 
        color: '#8ec6e3',
        fontSize: 11
      }
    },
    series: [{
      name: '电力消耗',
      type: 'bar',
      data: rankingData.map(r => r.value),
      barWidth: '60%',
      itemStyle: {
        color: (params) => {
          const building = buildings.value.find(b => b.building_id === rankingData[params.dataIndex].id)
          if (building?.energy_level === 'high') {
            return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: '#ff6b6b' },
              { offset: 1, color: '#ff8e8e' }
            ])
          } else if (building?.energy_level === 'medium') {
            return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: '#ffcc00' },
              { offset: 1, color: '#ffd633' }
            ])
          } else {
            return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: '#0066cc' },
              { offset: 1, color: '#00d4ff' }
            ])
          }
        },
        borderRadius: [0, 4, 4, 0]
      },
      label: {
        show: true,
        position: 'right',
        color: '#00d4ff',
        formatter: (params) => formatNumber(params.value)
      }
    }]
  })

  trendChartInstance.setOption({
    ...chartTheme,
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0,0,0,0.8)',
      borderColor: '#00d4ff',
      textStyle: { color: '#fff' }
    },
    legend: {
      data: ['电力消耗', 'HVAC能耗', '用水量'],
      textStyle: { color: '#8ec6e3' },
      top: 5
    },
    grid: {
      left: '12%',
      right: '5%',
      top: '20%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'],
      axisLine: { lineStyle: { color: '#1e4d6b' } },
      axisLabel: { color: '#8ec6e3' }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#1e4d6b' } },
      axisLabel: { color: '#8ec6e3' },
      splitLine: { lineStyle: { color: '#1e4d6b', type: 'dashed' } }
    },
    series: [
      {
        name: '电力消耗',
        type: 'line',
        smooth: true,
        data: [1200, 1100, 1500, 1800, 2100, 1900, 1400],
        lineStyle: { color: '#00d4ff', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0,212,255,0.3)' },
            { offset: 1, color: 'rgba(0,212,255,0.05)' }
          ])
        },
        itemStyle: { color: '#00d4ff' }
      },
      {
        name: 'HVAC能耗',
        type: 'line',
        smooth: true,
        data: [600, 550, 800, 1000, 1200, 1100, 700],
        lineStyle: { color: '#00ff88', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0,255,136,0.3)' },
            { offset: 1, color: 'rgba(0,255,136,0.05)' }
          ])
        },
        itemStyle: { color: '#00ff88' }
      },
      {
        name: '用水量',
        type: 'line',
        smooth: true,
        data: [50, 45, 70, 90, 100, 85, 60],
        lineStyle: { color: '#ffcc00', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255,204,0,0.3)' },
            { offset: 1, color: 'rgba(255,204,0,0.05)' }
          ])
        },
        itemStyle: { color: '#ffcc00' }
      }
    ]
  })

  pieChartInstance.setOption({
    ...chartTheme,
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0,0,0,0.8)',
      borderColor: '#00d4ff',
      textStyle: { color: '#fff' }
    },
    legend: {
      orient: 'vertical',
      left: '0%',
      top: '5%',
      textStyle: { color: '#8ec6e3' }
    },
    series: [{
      name: '能耗分布',
      type: 'pie',
      radius: ['40%', '80%'],
      center: ['60%', '53%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 8,
        borderColor: '#0a1628',
        borderWidth: 2
      },
      label: {
        show: true,
        formatter: '{d}%',
        color: '#8ec6e3',
        fontSize: 12
      },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold' }
      },
      data: [
        { value: 45, name: 'HVAC系统', itemStyle: { color: '#00d4ff' } },
        { value: 25, name: '照明系统', itemStyle: { color: '#00ff88' } },
        { value: 15, name: '办公设备', itemStyle: { color: '#ffcc00' } },
        { value: 10, name: '电梯系统', itemStyle: { color: '#ff6b6b' } },
        { value: 5, name: '其他', itemStyle: { color: '#a855f7' } }
      ]
    }]
  })
}

const handleResize = () => {
  trendChartInstance?.resize()
  pieChartInstance?.resize()
  rankingChartInstance?.resize()
}

const simulateRealtimeData = () => {
  realtimeData.value.electricity = 14000 + Math.random() * 3000
  realtimeData.value.water = 1100 + Math.random() * 300
  realtimeData.value.hvac = 7500 + Math.random() * 2000
  realtimeData.value.cop = (3.8 + Math.random() * 0.8).toFixed(1)
}

onMounted(async () => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
  
  await loadData()
  await loadBuildings()
  await initCharts()
  
  window.addEventListener('resize', handleResize)
  
  setInterval(simulateRealtimeData, 5000)
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.dashboard-screen {
  width: 100%;
  height: 100vh;
  color: #fff;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* 3D模型全屏背景 */
.building-simulation-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  background: linear-gradient(135deg, #0a1628 0%, #1a2a4a 50%, #0d1f3c 100%);
  pointer-events: auto !important;
}

.building-simulation-fullscreen * {
  pointer-events: auto !important;
}

.dashboard-header {
  height: 80px;
  background: linear-gradient(90deg, rgba(0, 100, 200, 0.3) 0%, rgba(0, 150, 255, 0.2) 50%, rgba(0, 100, 200, 0.3) 100%);
  border-bottom: 1px solid rgba(0, 212, 255, 0.3);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 30px;
  position: relative;
  z-index: 5;
  pointer-events: none;
}

.header-left, .header-center, .header-right, .nav-dropdown, .weather-info {
  pointer-events: auto;
}

.dashboard-header::before {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00d4ff, transparent);
}

.header-left, .header-right {
  width: 250px;
}

.current-time {
  font-size: 28px;
  font-weight: bold;
  color: #00d4ff;
  font-family: 'Courier New', monospace;
}

.current-date {
  font-size: 14px;
  color: #8ec6e3;
  margin-top: 5px;
}

.header-center {
  text-align: center;
}

.system-title {
  font-size: 28px;
  font-weight: bold;
  background: linear-gradient(90deg, #00d4ff, #00ff88);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  letter-spacing: 4px;
}

.system-subtitle {
  font-size: 12px;
  color: #8ec6e3;
  margin: 5px 0 0;
  letter-spacing: 2px;
}

.header-right {
  text-align: right;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 20px;
}

.weather-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  margin-top: 10px;
}

.weather-info .el-icon {
  font-size: 24px;
  color: #ffcc00;
}

.weather-desc {
  color: #8ec6e3;
}

.nav-dropdown {
  margin-left: 10px;
}

.nav-btn {
  background: linear-gradient(135deg, #0066cc, #00d4ff) !important;
  border: 1px solid rgba(0, 212, 255, 0.5) !important;
  color: #fff !important;
  font-weight: bold;
  transition: all 0.3s;
}

.nav-btn:hover {
  background: linear-gradient(135deg, #0080ff, #00e6ff) !important;
  border-color: #00d4ff !important;
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
}

:deep(.el-dropdown-menu) {
  background: rgba(10, 30, 60, 0.95) !important;
  border: 1px solid rgba(0, 212, 255, 0.3) !important;
  backdrop-filter: blur(10px);
}

:deep(.el-dropdown-menu__item) {
  color: #8ec6e3 !important;
  padding: 10px 20px;
  transition: all 0.3s;
}

:deep(.el-dropdown-menu__item:hover) {
  background: rgba(0, 212, 255, 0.2) !important;
  color: #00d4ff !important;
}

:deep(.el-dropdown-menu__item .el-icon) {
  margin-right: 8px;
  color: #00d4ff;
}

.dashboard-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px;
  gap: 20px;
  overflow: hidden;
  position: relative;
  z-index: 5;
  pointer-events: none; /* 整个内容区域让鼠标事件穿透到3D模型 */
}

.left-panel {
  width: 460px;
  display: flex;
  flex-direction: column;
  gap: 15px;
  pointer-events: auto; /* 只有左右面板可以交互 */
  flex-shrink: 0;
}

.right-panel {
  width: 400px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  pointer-events: auto; /* 只有左右面板可以交互 */
  flex-shrink: 0;
}

.center-bottom {
  height: 320px;
}

.panel-section {
  background: linear-gradient(180deg, rgba(0, 50, 100, 0.4) 0%, rgba(0, 30, 60, 0.3) 100%);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  padding: 12px;
  position: relative;
  overflow: hidden;
}

.panel-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00d4ff, transparent);
}

.map-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.ranking-section {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.ranking-hint {
  font-size: 12px;
  color: #8ec6e3;
  margin-left: auto;
  font-weight: normal;
}

.building-simulation {
  flex: 1;
  position: relative;
  background: radial-gradient(ellipse at center, rgba(0, 80, 150, 0.15) 0%, transparent 70%);
  border-radius: 12px;
  overflow: hidden;
  min-height: 450px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.simulation-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.grid-floor {
  position: absolute;
  bottom: 10%;
  left: 5%;
  right: 5%;
  height: 60%;
  background: 
    linear-gradient(90deg, rgba(0, 212, 255, 0.1) 1px, transparent 1px),
    linear-gradient(rgba(0, 212, 255, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
  transform: perspective(500px) rotateX(60deg);
  transform-origin: center bottom;
  opacity: 0.5;
}

.radar-system {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 0;
}

.radar-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 10px;
  height: 10px;
  background: #00d4ff;
  border-radius: 50%;
  box-shadow: 0 0 20px #00d4ff, 0 0 40px #00d4ff;
  animation: radar-center-pulse 2s ease-in-out infinite;
}

.radar-scan {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 600px;
  height: 600px;
  border: 1px solid transparent;
  border-top: 2px solid rgba(0, 212, 255, 0.8);
  border-radius: 50%;
  animation: radar-scan 4s linear infinite;
}

.radar-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 50%;
  animation: radar-pulse 3s ease-out infinite;
}

.radar-ring.ring-1 {
  width: 200px;
  height: 200px;
  animation-delay: 0s;
}

.radar-ring.ring-2 {
  width: 400px;
  height: 400px;
  animation-delay: 1s;
}

.radar-ring.ring-3 {
  width: 600px;
  height: 600px;
  animation-delay: 2s;
}

@keyframes radar-center-pulse {
  0%, 100% {
    transform: translate(-50%, -50%) scale(1);
    box-shadow: 0 0 20px #00d4ff, 0 0 40px #00d4ff;
  }
  50% {
    transform: translate(-50%, -50%) scale(1.2);
    box-shadow: 0 0 30px #00d4ff, 0 0 60px #00d4ff;
  }
}

@keyframes radar-scan {
  0% {
    transform: translate(-50%, -50%) rotate(0deg);
  }
  100% {
    transform: translate(-50%, -50%) rotate(360deg);
  }
}

@keyframes radar-pulse {
  0% {
    opacity: 0.8;
    transform: translate(-50%, -50%) scale(0.8);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(1.5);
  }
}

.buildings-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 60px;
}

.building-3d {
  position: absolute;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 1;
}

.building-3d:hover {
  z-index: 100;
  transform: translate(-50%, -50%) scale(1.1) rotateX(-5deg) rotateY(-10deg);
}

.building-3d:hover .building-glow {
  opacity: 1;
  box-shadow: 0 0 40px var(--building-color);
}

.building-3d:hover .energy-ring {
  animation: ring-pulse 1s ease-in-out infinite;
}

.building-3d:hover .energy-flow {
  animation: energy-flow-intense 1.5s ease-in-out infinite;
}

.building-structure {
  position: relative;
  transform-style: preserve-3d;
  transform: rotateX(-10deg) rotateY(-20deg);
  transition: transform 0.3s ease;
}

.building-3d:hover .building-structure {
  transform: rotateX(-5deg) rotateY(-15deg);
}

.building-front {
  width: 30px;
  background: linear-gradient(180deg, var(--building-color) 0%, var(--building-color-dark) 100%);
  border-radius: 2px 2px 0 0;
  position: relative;
  box-shadow: 
    inset 0 0 20px rgba(255, 255, 255, 0.1),
    0 5px 15px rgba(0, 0, 0, 0.3),
    0 0 30px rgba(0, 212, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
}

.building-front::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  animation: scan-line 3s ease-in-out infinite;
}

@keyframes scan-line {
  0% { transform: translateY(-100%); }
  100% { transform: translateY(200%); }
}

.building-side {
  width: 15px;
  background: linear-gradient(180deg, var(--building-color-dark) 0%, var(--building-color-darker) 100%);
  position: absolute;
  right: -14px;
  top: 0;
  transform: skewY(-45deg);
  transform-origin: left top;
  border-radius: 0 4px 0 0;
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-left: none;
}

.building-top {
  width: 30px;
  height: 15px;
  background: var(--building-color-light);
  position: absolute;
  top: -7px;
  left: 0;
  transform: skewX(-45deg);
  transform-origin: left bottom;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-bottom: none;
  border-right: none;
  position: relative;
}

/* 建筑顶部设备 */
.building-top::after {
  content: '';
  position: absolute;
  top: -15px;
  left: 50%;
  transform: translateX(-50%) skewX(45deg);
  width: 3px;
  height: 12px;
  background: var(--building-color-dark);
  border-radius: 2px 2px 0 0;
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
  animation: antenna-glow 2s ease-in-out infinite;
}

.building-top::before {
  content: '';
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%) skewX(45deg);
  width: 8px;
  height: 4px;
  background: #00d4ff;
  border-radius: 50%;
  box-shadow: 0 0 15px #00d4ff;
  animation: satellite-pulse 3s ease-in-out infinite;
}

@keyframes antenna-glow {
  0%, 100% { box-shadow: 0 0 10px rgba(0, 212, 255, 0.5); }
  50% { box-shadow: 0 0 20px rgba(0, 212, 255, 0.8); }
}

@keyframes satellite-pulse {
  0%, 100% { transform: translateX(-50%) skewX(45deg) scale(1); box-shadow: 0 0 15px #00d4ff; }
  50% { transform: translateX(-50%) skewX(45deg) scale(1.2); box-shadow: 0 0 25px #00d4ff; }
}

.building-back {
  width: 30px;
  height: 100%;
  background: linear-gradient(180deg, var(--building-color-dark) 0%, var(--building-color-darker) 100%);
  position: absolute;
  left: 0;
  top: 0;
  transform: translateZ(-14px);
  border-radius: 2px 2px 0 0;
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-left: none;
}

.building-left {
  width: 14px;
  height: 100%;
  background: linear-gradient(180deg, var(--building-color-dark) 0%, var(--building-color-darker) 100%);
  position: absolute;
  left: -14px;
  top: 0;
  transform: skewY(45deg);
  transform-origin: right top;
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-right: none;
}

.building-windows {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 4px;
  padding: 6px 4px;
}

.window {
  width: 8px;
  height: 6px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 1px;
  animation: window-blink 3s ease-in-out infinite;
}

@keyframes window-blink {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

.building-reflection {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%) scaleY(-1);
  width: 35px;
  background: linear-gradient(to bottom, var(--building-color), transparent);
  opacity: 0.2;
  filter: blur(3px);
  border-radius: 0 0 4px 4px;
}

.building-glow {
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 50px;
  height: 20px;
  border-radius: 50%;
  filter: blur(15px);
  opacity: 0.6;
  transition: all 0.3s;
}

.energy-ring {
  position: absolute;
  bottom: -25px;
  left: 50%;
  transform: translateX(-50%);
  border: 2px solid;
  border-radius: 50%;
  opacity: 0.3;
}

@keyframes ring-pulse {
  0%, 100% { transform: translateX(-50%) scale(1); opacity: 0.3; }
  50% { transform: translateX(-50%) scale(1.2); opacity: 0.6; }
}

.energy-flow {
  position: absolute;
  top: -10px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 5;
  width: 20px;
  height: 100px;
}

.energy-particle {
  position: absolute;
  width: 8px;
  height: 8px;
  background: var(--building-color);
  border-radius: 50%;
  animation: energy-flow 3s ease-in-out infinite;
  box-shadow: 0 0 15px var(--building-color);
  left: 50%;
  transform: translateX(-50%);
}

.energy-particle:nth-child(2) {
  animation-delay: 0.5s;
  width: 6px;
  height: 6px;
  box-shadow: 0 0 10px var(--building-color);
}

.energy-particle:nth-child(3) {
  animation-delay: 1s;
  width: 10px;
  height: 10px;
  box-shadow: 0 0 20px var(--building-color);
}

@keyframes energy-flow {
  0% {
    transform: translateX(-50%) translateY(0) scale(1);
    opacity: 0;
  }
  25% {
    opacity: 1;
    box-shadow: 0 0 25px var(--building-color);
  }
  50% {
    transform: translateX(-50%) translateY(-30px) scale(1.2);
    box-shadow: 0 0 30px var(--building-color);
  }
  75% {
    opacity: 0.8;
  }
  100% {
    transform: translateX(-50%) translateY(-80px) scale(0.3);
    opacity: 0;
  }
}

@keyframes energy-flow-intense {
  0% {
    transform: translateX(-50%) translateY(0) scale(1);
    opacity: 0;
  }
  25% {
    opacity: 1;
    box-shadow: 0 0 30px var(--building-color);
  }
  50% {
    transform: translateX(-50%) translateY(-40px) scale(1.5);
    box-shadow: 0 0 40px var(--building-color);
  }
  75% {
    opacity: 0.6;
  }
  100% {
    transform: translateX(-50%) translateY(-100px) scale(0.2);
    opacity: 0;
  }
}

.road-network {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: -1;
}

.road {
  position: absolute;
  background: linear-gradient(90deg, transparent, rgba(100, 150, 200, 0.4), transparent);
  border-radius: 2px;
  box-shadow: 0 0 10px rgba(100, 150, 200, 0.3);
  animation: road-glow 3s ease-in-out infinite;
}

.road.main-road {
  top: 45%;
  left: 5%;
  right: 95%;
  height: 10px;
  transform: skewX(-5deg);
  background: linear-gradient(90deg, transparent, rgba(100, 180, 255, 0.5), transparent);
}

.road.cross-road {
  top: 10%;
  bottom: 90%;
  left: 50%;
  width: 8px;
  transform: skewY(-5deg);
  background: linear-gradient(180deg, transparent, rgba(100, 180, 255, 0.5), transparent);
}

.road.side-road {
  top: 75%;
  left: 15%;
  right: 70%;
  height: 6px;
  transform: skewX(3deg);
  background: linear-gradient(90deg, transparent, rgba(100, 160, 220, 0.4), transparent);
}

.road.diagonal-road {
  top: 20%;
  left: 10%;
  width: 6px;
  height: 400px;
  transform: skewX(30deg);
  background: linear-gradient(180deg, transparent, rgba(100, 160, 220, 0.4), transparent);
}

.road.ring-road {
  top: 30%;
  left: 30%;
  right: 30%;
  bottom: 30%;
  border: 3px solid rgba(100, 180, 255, 0.3);
  border-radius: 50%;
  background: none;
  animation: ring-road-pulse 4s ease-in-out infinite;
}

@keyframes road-glow {
  0%, 100% { opacity: 0.6; box-shadow: 0 0 10px rgba(100, 150, 200, 0.3); }
  50% { opacity: 1; box-shadow: 0 0 20px rgba(100, 150, 200, 0.6); }
}

@keyframes ring-road-pulse {
  0%, 100% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.05); opacity: 0.6; }
}

.green-areas {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: -2;
}

.green-area {
  position: absolute;
  background: linear-gradient(135deg, rgba(0, 255, 100, 0.1), rgba(0, 200, 80, 0.05));
  border-radius: 50%;
  filter: blur(10px);
  animation: green-pulse 4s ease-in-out infinite;
}

.green-area.area-1 {
  top: 20%;
  left: 80%;
  width: 100px;
  height: 80px;
  animation-delay: 0s;
}

.green-area.area-2 {
  top: 60%;
  left: 10%;
  width: 120px;
  height: 100px;
  animation-delay: 1s;
}

.green-area.area-3 {
  top: 80%;
  left: 50%;
  width: 80px;
  height: 60px;
  animation-delay: 2s;
}

.green-area.area-4 {
  top: 30%;
  left: 30%;
  width: 90px;
  height: 70px;
  animation-delay: 3s;
}

.background-decorations {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: -3;
}

.decoration {
  position: absolute;
  background: linear-gradient(45deg, transparent, rgba(0, 212, 255, 0.1), transparent);
  border-radius: 50%;
  animation: decoration-float 6s ease-in-out infinite;
}

.decoration.decoration-1 {
  top: 10%;
  right: 15%;
  width: 150px;
  height: 150px;
  animation-delay: 0s;
}

.decoration.decoration-2 {
  bottom: 15%;
  left: 10%;
  width: 120px;
  height: 120px;
  animation-delay: 2s;
}

.decoration.decoration-3 {
  top: 40%;
  left: 5%;
  width: 80px;
  height: 80px;
  animation-delay: 4s;
}

@keyframes green-pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.6;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.8;
  }
}

@keyframes decoration-float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
    opacity: 0.3;
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
    opacity: 0.6;
  }
}

.building-structure.commercial .building-front {
  width: 35px;
  background: linear-gradient(180deg, var(--building-color) 0%, var(--building-color-dark) 100%);
  box-shadow: 
    inset 0 0 30px rgba(255, 255, 255, 0.15),
    0 5px 20px rgba(0, 0, 0, 0.4),
    0 0 40px rgba(0, 212, 255, 0.3);
}

.building-structure.commercial .building-top {
  width: 35px;
  height: 18px;
  background: var(--building-color-light);
}

.building-structure.hospital .building-front {
  width: 25px;
  background: linear-gradient(180deg, var(--building-color) 0%, var(--building-color-dark) 100%);
  box-shadow: 
    inset 0 0 20px rgba(255, 255, 255, 0.1),
    0 5px 15px rgba(0, 0, 0, 0.3),
    0 0 30px rgba(255, 107, 107, 0.3);
}

.building-structure.hospital .building-top {
  width: 25px;
  height: 12px;
  background: var(--building-color-light);
}

.building-structure.hotel .building-front {
  width: 32px;
  border-radius: 8px 8px 0 0;
  background: linear-gradient(180deg, var(--building-color) 0%, var(--building-color-dark) 100%);
  box-shadow: 
    inset 0 0 25px rgba(255, 255, 255, 0.12),
    0 5px 18px rgba(0, 0, 0, 0.35),
    0 0 35px rgba(255, 204, 0, 0.25);
}

.building-structure.hotel .building-top {
  width: 32px;
  height: 16px;
  border-radius: 8px 8px 0 0;
  background: var(--building-color-light);
}

.building-structure.residential .building-front {
  width: 28px;
  border-radius: 4px 4px 0 0;
  background: linear-gradient(180deg, var(--building-color) 0%, var(--building-color-dark) 100%);
  box-shadow: 
    inset 0 0 20px rgba(255, 255, 255, 0.1),
    0 5px 15px rgba(0, 0, 0, 0.3),
    0 0 25px rgba(0, 255, 136, 0.2);
}

.building-structure.residential .building-top {
  width: 28px;
  height: 14px;
  border-radius: 4px 4px 0 0;
  background: var(--building-color-light);
}

.building-structure.office .building-front {
  width: 30px;
  border-radius: 2px 2px 0 0;
  background: linear-gradient(180deg, var(--building-color) 0%, var(--building-color-dark) 100%);
  box-shadow: 
    inset 0 0 25px rgba(255, 255, 255, 0.12),
    0 5px 18px rgba(0, 0, 0, 0.35),
    0 0 35px rgba(0, 212, 255, 0.25);
}

.building-structure.office .building-top {
  width: 30px;
  height: 15px;
  background: var(--building-color-light);
}

/* 特殊建筑效果 */
.building-structure.commercial::before {
  content: '';
  position: absolute;
  top: -15px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 10px;
  background: linear-gradient(180deg, #ffcc00, #ff9900);
  border-radius: 2px;
  box-shadow: 0 0 15px rgba(255, 204, 0, 0.6);
  animation: commercial-sign 2s ease-in-out infinite;
}

.building-structure.hospital::before {
  content: '';
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  width: 15px;
  height: 15px;
  background: #ff6b6b;
  border-radius: 50%;
  box-shadow: 0 0 15px rgba(255, 107, 107, 0.6);
  animation: hospital-sign 2s ease-in-out infinite;
}

.building-structure.hotel::before {
  content: '';
  position: absolute;
  top: -18px;
  left: 50%;
  transform: translateX(-50%);
  width: 18px;
  height: 8px;
  background: linear-gradient(180deg, #00d4ff, #0088cc);
  border-radius: 4px;
  box-shadow: 0 0 12px rgba(0, 212, 255, 0.5);
  animation: hotel-sign 2.5s ease-in-out infinite;
}

.building-structure.residential::before {
  content: '';
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  width: 12px;
  height: 6px;
  background: linear-gradient(180deg, #00ff88, #00cc66);
  border-radius: 3px;
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.4);
  animation: residential-sign 3s ease-in-out infinite;
}

@keyframes commercial-sign {
  0%, 100% { transform: translateX(-50%) scale(1); box-shadow: 0 0 15px rgba(255, 204, 0, 0.6); }
  50% { transform: translateX(-50%) scale(1.1); box-shadow: 0 0 25px rgba(255, 204, 0, 0.8); }
}

@keyframes hospital-sign {
  0%, 100% { transform: translateX(-50%) scale(1); box-shadow: 0 0 15px rgba(255, 107, 107, 0.6); }
  50% { transform: translateX(-50%) scale(1.1); box-shadow: 0 0 25px rgba(255, 107, 107, 0.8); }
}

@keyframes hotel-sign {
  0%, 100% { transform: translateX(-50%) scale(1); box-shadow: 0 0 12px rgba(0, 212, 255, 0.5); }
  50% { transform: translateX(-50%) scale(1.1); box-shadow: 0 0 20px rgba(0, 212, 255, 0.7); }
}

@keyframes residential-sign {
  0%, 100% { transform: translateX(-50%) scale(1); box-shadow: 0 0 10px rgba(0, 255, 136, 0.4); }
  50% { transform: translateX(-50%) scale(1.1); box-shadow: 0 0 18px rgba(0, 255, 136, 0.6); }
}

.connection-line {
  animation: line-pulse 3s ease-in-out infinite;
}

@keyframes line-pulse {
  0%, 100% { opacity: 0.2; }
  50% { opacity: 0.6; }
}

.building-3d.energy-high {
  --building-color: #ff6b6b;
  --building-color-light: #ff8e8e;
  --building-color-dark: #cc4444;
  --building-color-darker: #992222;
}

.building-3d.energy-high .building-glow {
  background: #ff6b6b;
}

.building-3d.energy-high .energy-ring {
  border-color: #ff6b6b;
}

.building-3d.energy-medium {
  --building-color: #ffcc00;
  --building-color-light: #ffd633;
  --building-color-dark: #cc9900;
  --building-color-darker: #996600;
}

.building-3d.energy-medium .building-glow {
  background: #ffcc00;
}

.building-3d.energy-medium .energy-ring {
  border-color: #ffcc00;
}

.building-3d.energy-low {
  --building-color: #00d4ff;
  --building-color-light: #4de3ff;
  --building-color-dark: #0088cc;
  --building-color-darker: #005588;
}

.building-3d.energy-low .building-glow {
  background: #00d4ff;
}

.building-3d.energy-low .energy-ring {
  border-color: #00d4ff;
}

.building-label {
  position: absolute;
  top: calc(100% + 50px);
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  white-space: nowrap;
  z-index: 10;
}

.label-name {
  display: block;
  font-size: 10px;
  font-weight: bold;
  color: #fff;
  text-shadow: 0 0 10px rgba(0, 0, 0, 0.8);
}

.label-value {
  display: block;
  font-size: 9px;
  color: #00d4ff;
  margin-top: 2px;
}

.building-detail-card {
  position: absolute;
  bottom: calc(100% + 50px);
  left: 50%;
  transform: translateX(-50%);
  background: rgba(10, 25, 50, 0.98);
  border: 1px solid rgba(0, 212, 255, 0.5);
  border-radius: 12px;
  padding: 0;
  min-width: 220px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6), 0 0 20px rgba(0, 212, 255, 0.2);
  z-index: 200;
  backdrop-filter: blur(10px);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background: linear-gradient(90deg, rgba(0, 100, 200, 0.3), rgba(0, 150, 255, 0.2));
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
}

.card-title {
  font-size: 14px;
  font-weight: bold;
  color: #00d4ff;
}

.card-status {
  font-size: 10px;
  padding: 3px 8px;
  border-radius: 10px;
  font-weight: bold;
}

.card-status.status-high {
  background: rgba(255, 107, 107, 0.2);
  color: #ff6b6b;
}

.card-status.status-medium {
  background: rgba(255, 204, 0, 0.2);
  color: #ffcc00;
}

.card-status.status-low {
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
}

.card-body {
  padding: 12px 15px;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 0;
  font-size: 12px;
}

.detail-icon {
  color: #00d4ff;
  font-size: 14px;
}

.detail-label {
  color: #8ec6e3;
  min-width: 60px;
}

.detail-value {
  color: #fff;
  font-weight: bold;
  margin-left: auto;
}

.detail-value.highlight {
  color: #00ff88;
}

.card-footer {
  padding: 10px 15px;
  border-top: 1px solid rgba(0, 212, 255, 0.2);
  text-align: center;
}

.card-footer .el-button {
  background: linear-gradient(135deg, #0066cc, #00d4ff) !important;
  border: none !important;
}

.tooltip-fade-enter-active,
.tooltip-fade-leave-active {
  transition: all 0.2s ease;
}

.tooltip-fade-enter-from,
.tooltip-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}

.connection-lines {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
}

.connections-svg {
  width: 100%;
  height: 100%;
}

.map-stats {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 30px;
  background: rgba(0, 30, 60, 0.8);
  padding: 10px 25px;
  border-radius: 20px;
  border: 1px solid rgba(0, 212, 255, 0.3);
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #00d4ff;
}

.stat-value.high-count {
  color: #ff6b6b;
}

.stat-value.medium-count {
  color: #ffcc00;
}

.stat-value.low-count {
  color: #00d4ff;
}

.stat-label {
  font-size: 10px;
  color: #8ec6e3;
  margin-top: 2px;
}

.section-title {
  font-size: 16px;
  font-weight: bold;
  color: #00d4ff;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  width: 4px;
  height: 16px;
  background: linear-gradient(180deg, #00d4ff, #00ff88);
  border-radius: 2px;
}

.chart-box {
  height: 150px;
  width: 100%;
}

.chart-box-trend {
  height: 180px;
  width: 100%;
}

.chart-box-ranking {
  flex: 1;
  width: 100%;
  min-height: 300px;
}

.energy-overview {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.energy-item {
  background: linear-gradient(180deg, rgba(0, 50, 100, 0.3) 0%, rgba(0, 30, 60, 0.2) 100%);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s ease;
}

.energy-item:hover {
  border-color: #00d4ff;
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}

.energy-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #fff;
}

.energy-icon.electricity {
  background: linear-gradient(135deg, #00d4ff, #0066cc);
}

.energy-icon.water {
  background: linear-gradient(135deg, #00ff88, #009966);
}

.energy-icon.hvac {
  background: linear-gradient(135deg, #ffcc00, #cc9900);
}

.energy-icon.cop {
  background: linear-gradient(135deg, #a855f7, #7e22ce);
}

.energy-info {
  flex: 1;
}

.energy-value {
  font-size: 18px;
  font-weight: bold;
  color: #fff;
}

.energy-unit {
  font-size: 10px;
  color: #8ec6e3;
  margin-top: 2px;
}

.energy-label {
  font-size: 12px;
  color: #8ec6e3;
  margin-top: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.energy-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: bold;
}

.energy-trend.up {
  color: #ff6b6b;
}

.energy-trend.down {
  color: #00ff88;
}

.energy-trend.stable {
  color: #00d4ff;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.status-item {
  background: linear-gradient(180deg, rgba(0, 50, 100, 0.3) 0%, rgba(0, 30, 60, 0.2) 100%);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s ease;
}

.status-item.active {
  border-color: #00ff88;
  box-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
}

.status-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: linear-gradient(135deg, #00d4ff, #0066cc);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: #fff;
}

.status-name {
  font-size: 12px;
  color: #8ec6e3;
  margin-bottom: 4px;
}

.status-value {
  font-size: 14px;
  font-weight: bold;
  color: #fff;
}

.alarm-list {
  max-height: 200px;
  overflow-y: auto;
}

.alarm-item {
  background: linear-gradient(180deg, rgba(0, 50, 100, 0.3) 0%, rgba(0, 30, 60, 0.2) 100%);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s ease;
  max-width: 97%;
}

.alarm-item:hover {
  border-color: #00d4ff;
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.3);
}

.alarm-item.error {
  border-left: 4px solid #ff6b6b;
}

.alarm-item.warning {
  border-left: 4px solid #ffcc00;
}

.alarm-item.info {
  border-left: 4px solid #00d4ff;
}

.alarm-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(255, 107, 107, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #ff6b6b;
}

.alarm-item.warning .alarm-icon {
  background: rgba(255, 204, 0, 0.2);
  color: #ffcc00;
}

.alarm-item.info .alarm-icon {
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
}

.alarm-title {
  font-size: 12px;
  font-weight: bold;
  color: #fff;
  margin-bottom: 4px;
}

.alarm-time {
  font-size: 10px;
  color: #8ec6e3;
}

.no-alarm {
  text-align: center;
  padding: 30px 0;
  color: #00ff88;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.env-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.env-item {
  background: linear-gradient(180deg, rgba(0, 50, 100, 0.3) 0%, rgba(0, 30, 60, 0.2) 100%);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  transition: all 0.3s ease;
}

.env-item:hover {
  border-color: #00d4ff;
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.3);
}

.env-label {
  font-size: 12px;
  color: #8ec6e3;
  margin-bottom: 8px;
}

.env-value {
  font-size: 18px;
  font-weight: bold;
  color: #00d4ff;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 30, 60, 0.5);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: rgba(0, 212, 255, 0.5);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 212, 255, 0.8);
}

/* 响应式设计 */
@media screen and (max-width: 1200px) {
  .left-panel, .right-panel {
    width: 300px;
  }
  
  .energy-overview {
    grid-template-columns: 1fr;
  }
  
  .status-grid, .env-grid {
    grid-template-columns: 1fr;
  }
}

@media screen and (max-width: 992px) {
  .dashboard-content {
    flex-direction: column;
    overflow-y: auto;
  }
  
  .left-panel, .right-panel {
    width: 100%;
    flex-direction: row;
    flex-wrap: wrap;
  }
  
  .panel-section {
    flex: 1;
    min-width: 300px;
  }
  
  .center-panel {
    order: -1;
  }
}
</style>