/**
 * Vue.js 实时监测组件
 * 可集成到任何 Vue 3 项目
 * 
 * 使用方式：
 * 1. npm install
 * 2. 在 main.js 中注册组件
 * 3. 在页面中使用 <RealTimeMonitor />
 */

<template>
  <div class="monitor-container">
    <!-- 顶部状态栏 -->
    <div class="monitor-header">
      <div class="status-info">
        <span class="status-dot" :class="statusClass"></span>
        <span class="status-text">{{ statusText }}</span>
      </div>
      <div class="sim-time">{{ simTimeText }}</div>
      <div class="speed-info" v-if="isRunning">
        速度: {{ currentSpeed }}x (1秒={{ speedTimeText }})
      </div>
      <div class="controls">
        <button v-if="!isRunning" class="btn btn-primary" @click="start">▶ 启动</button>
        <button v-if="isRunning && !isPaused" class="btn btn-warning" @click="pause">⏸ 暂停</button>
        <button v-if="isPaused" class="btn btn-primary" @click="resume">▶ 继续</button>
        <button v-if="isRunning" class="btn btn-danger" @click="stop">⏹ 停止</button>
        <button class="btn btn-secondary" @click="reset">🔄 重置</button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card total">
        <div class="value">{{ buildingCount }}</div>
        <div class="label">监测建筑</div>
      </div>
      <div class="stat-card normal">
        <div class="value">{{ normalCount }}</div>
        <div class="label">正常运行</div>
      </div>
      <div class="stat-card warning">
        <div class="value">{{ warningCount }}</div>
        <div class="label">警告状态</div>
      </div>
      <div class="stat-card critical">
        <div class="value">{{ criticalCount }}</div>
        <div class="label">异常告警</div>
      </div>
    </div>

    <!-- 主体内容 -->
    <div class="monitor-main">
      <!-- 控制面板 -->
      <div class="control-panel">
        <h3>🎛 监测控制</h3>
        
        <div class="control-group">
          <label>起始日期</label>
          <input type="date" v-model="startDate" />
        </div>
        
        <div class="control-group">
          <label>时间加速倍率</label>
          <div class="speed-buttons">
            <button 
              v-for="s in speeds" 
              :key="s.value"
              :class="['speed-btn', { active: currentSpeed === s.value }]"
              @click="setSpeed(s.value)"
            >
              {{ s.label }}<br><small>{{ s.desc }}</small>
            </button>
          </div>
        </div>

        <!-- 异常模拟 -->
        <div class="anomaly-section">
          <h4>🧪 异常模拟</h4>
          <div class="control-group">
            <label>目标建筑</label>
            <select v-model="simBuilding">
              <option value="all">所有建筑</option>
              <option v-for="b in buildings" :key="b" :value="b">{{ b }}</option>
            </select>
          </div>
          <div class="control-group">
            <label>异常类型</label>
            <select v-model="simType">
              <option value="electricity_high">电耗过高</option>
              <option value="electricity_low">电耗过低</option>
              <option value="temp_high">温度异常高</option>
              <option value="temp_low">温度异常低</option>
              <option value="random">随机异常</option>
            </select>
          </div>
          <div class="control-group">
            <label>异常强度: {{ simIntensity }}</label>
            <input type="range" v-model="simIntensity" min="1" max="10" />
          </div>
          <button class="btn btn-secondary" @click="triggerAnomaly">触发异常</button>
        </div>
      </div>

      <!-- 建筑网格 -->
      <div class="buildings-section">
        <h3>建筑状态</h3>
        <div class="buildings-grid">
          <div 
            v-for="(info, name) in buildingStatus" 
            :key="name"
            :class="['building-card', info.status, { simulated: info.simulated }]"
            @click="showBuildingDetail(name)"
          >
            <div class="name">{{ name }}</div>
            <span :class="['status-badge', info.status]">
              {{ statusLabels[info.status] }}
              <span v-if="info.simulated" class="sim-tag">模拟</span>
            </span>
            <div class="data">
              <div><span>电耗</span><span>{{ formatValue(info.current_data?.electricity_kwh) }} kWh</span></div>
              <div><span>温度</span><span>{{ formatValue(info.current_data?.outdoor_temp) }} °C</span></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 告警面板 -->
      <div class="alerts-panel">
        <h3>
          实时告警
          <span class="alert-count">{{ alerts.length }}</span>
          <button class="btn-clear" @click="clearAlerts" title="清除所有告警">🗑️</button>
        </h3>
        <div class="alerts-list">
          <div v-if="alerts.length === 0" class="no-alerts">暂无告警</div>
          <div 
            v-for="alert in recentAlerts" 
            :key="alert.id"
            :class="['alert-item', alert.level, { simulated: alert.simulated }]"
          >
            <div class="alert-header">
              <span class="building">{{ alert.building_id }}</span>
              <span class="time">{{ alert.timestamp }}</span>
            </div>
            <div class="alert-message">{{ alert.message }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

// Props
const props = defineProps({
  apiBase: {
    type: String,
    default: 'http://localhost:8080'
  },
  buildings: {
    type: Array,
    default: () => ['Building1', 'Building2', 'Building3']
  }
})

// 状态
const isRunning = ref(false)
const isPaused = ref(false)
const currentSpeed = ref(60)
const startDate = ref('2021-07-01')
const simulationTime = ref(null)
const buildingStatus = ref({})
const alerts = ref([])

// 异常模拟
const simBuilding = ref('all')
const simType = ref('electricity_high')
const simIntensity = ref(5)

// WebSocket
let ws = null

// 速度选项
const speeds = [
  { value: 1, label: '1x', desc: '1秒=1分' },
  { value: 10, label: '10x', desc: '1秒=10分' },
  { value: 60, label: '60x', desc: '1秒=1时' },
  { value: 300, label: '300x', desc: '1秒=5时' },
  { value: 600, label: '600x', desc: '1秒=10时' }
]

// 计算属性
const statusClass = computed(() => {
  if (!isRunning.value) return 'stopped'
  if (isPaused.value) return 'paused'
  return 'running'
})

const statusText = computed(() => {
  if (!isRunning.value) return '已停止'
  if (isPaused.value) return '已暂停'
  return '监测中'
})

const simTimeText = computed(() => {
  if (!simulationTime.value) return '模拟时间: --:--:--'
  return '模拟时间: ' + simulationTime.value.replace('T', ' ').substring(0, 16)
})

const speedTimeText = computed(() => {
  if (currentSpeed.value < 60) return currentSpeed.value + '分钟'
  if (currentSpeed.value === 60) return '1小时'
  return (currentSpeed.value / 60) + '小时'
})

const buildingCount = computed(() => props.buildings.length)

const normalCount = computed(() => 
  Object.values(buildingStatus.value).filter(b => b.status === 'normal').length
)

const warningCount = computed(() => 
  Object.values(buildingStatus.value).filter(b => b.status === 'warning').length
)

const criticalCount = computed(() => 
  Object.values(buildingStatus.value).filter(b => b.status === 'critical').length
)

const recentAlerts = computed(() => alerts.value.slice(0, 30))

const statusLabels = {
  normal: '正常',
  warning: '警告',
  critical: '异常'
}

// 方法
function formatValue(val) {
  return val != null ? val.toFixed(1) : '--'
}

async function start() {
  try {
    await fetch(`${props.apiBase}/monitor/start?speed=${currentSpeed.value}&start_date=${startDate.value}`, {
      method: 'POST'
    })
  } catch (error) {
    console.error('启动失败:', error)
  }
}

async function stop() {
  try {
    await fetch(`${props.apiBase}/monitor/stop`, { method: 'POST' })
  } catch (error) {
    console.error('停止失败:', error)
  }
}

async function pause() {
  try {
    await fetch(`${props.apiBase}/monitor/pause`, { method: 'POST' })
  } catch (error) {
    console.error('暂停失败:', error)
  }
}

async function resume() {
  try {
    await fetch(`${props.apiBase}/monitor/resume`, { method: 'POST' })
  } catch (error) {
    console.error('继续失败:', error)
  }
}

async function reset() {
  if (!confirm('确定要重置监测吗？')) return
  try {
    await fetch(`${props.apiBase}/monitor/reset`, { method: 'POST' })
    alerts.value = []
    initBuildingStatus()
  } catch (error) {
    console.error('重置失败:', error)
  }
}

async function setSpeed(speed) {
  currentSpeed.value = speed
  if (isRunning.value) {
    try {
      await fetch(`${props.apiBase}/monitor/speed?speed=${speed}`, { method: 'POST' })
    } catch (error) {
      console.error('调速失败:', error)
    }
  }
}

async function triggerAnomaly() {
  try {
    await fetch(`${props.apiBase}/monitor/trigger-anomaly`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        building: simBuilding.value,
        type: simType.value,
        intensity: parseInt(simIntensity.value)
      })
    })
  } catch (error) {
    console.error('触发异常失败:', error)
  }
}

async function clearAlerts() {
  if (!confirm('确定要清除所有告警吗？')) return
  try {
    await fetch(`${props.apiBase}/monitor/clear-alerts`, { method: 'POST' })
    alerts.value = []
  } catch (error) {
    console.error('清除告警失败:', error)
  }
}

function showBuildingDetail(name) {
  const info = buildingStatus.value[name]
  if (info) {
    alert(`${name}\n状态: ${statusLabels[info.status]}\n数据: ${JSON.stringify(info.current_data, null, 2)}`)
  }
}

function initBuildingStatus() {
  const status = {}
  props.buildings.forEach(name => {
    status[name] = {
      building_id: name,
      status: 'normal',
      last_update: '',
      current_data: {},
      active_alerts: 0,
      simulated: false
    }
  })
  buildingStatus.value = status
}

function connectWebSocket() {
  ws = new WebSocket(`${props.apiBase.replace('http', 'ws')}/ws/monitor`)
  
  ws.onopen = () => {
    console.log('WebSocket 已连接')
  }
  
  ws.onclose = () => {
    console.log('WebSocket 已断开，5秒后重连')
    setTimeout(connectWebSocket, 5000)
  }
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    handleMessage(data)
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket 错误:', error)
  }
}

function handleMessage(data) {
  switch (data.type) {
    case 'update':
    case 'status':
      isRunning.value = data.is_running || false
      isPaused.value = data.is_paused || false
      if (data.speed) currentSpeed.value = data.speed
      if (data.simulation_time) simulationTime.value = data.simulation_time
      if (data.buildings) {
        buildingStatus.value = data.buildings
      }
      break
    case 'alert':
      alerts.value.unshift(data.data)
      if (alerts.value.length > 100) alerts.value.pop()
      break
    case 'monitoring_started':
      isRunning.value = true
      break
  }
}

// 定期获取状态
let statusInterval = null

onMounted(() => {
  initBuildingStatus()
  connectWebSocket()
  
  statusInterval = setInterval(async () => {
    try {
      const response = await fetch(`${props.apiBase}/monitor/status`)
      const data = await response.json()
      handleMessage(data)
    } catch (error) {
      console.error('获取状态失败:', error)
    }
  }, 3000)
})

onUnmounted(() => {
  if (ws) ws.close()
  if (statusInterval) clearInterval(statusInterval)
})
</script>

<style scoped>
.monitor-container {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #0a0a0a;
  color: #fff;
  min-height: 100vh;
  padding: 20px;
}

.monitor-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 12px;
  margin-bottom: 20px;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.status-dot.running { background: #4ade80; }
.status-dot.paused { background: #f59e0b; }
.status-dot.stopped { background: #6b7280; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.sim-time {
  font-family: monospace;
  font-size: 16px;
  color: #60a5fa;
}

.speed-info {
  font-size: 13px;
  color: #9ca3af;
  background: rgba(96, 165, 250, 0.1);
  padding: 4px 12px;
  border-radius: 6px;
}

.controls {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-primary { background: #667eea; color: white; }
.btn-warning { background: #f59e0b; color: white; }
.btn-danger { background: #ef4444; color: white; }
.btn-secondary { background: #374151; color: white; }

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.stat-card .value {
  font-size: 32px;
  font-weight: 700;
}

.stat-card.total .value { color: #60a5fa; }
.stat-card.normal .value { color: #4ade80; }
.stat-card.warning .value { color: #fbbf24; }
.stat-card.critical .value { color: #f87171; }

.stat-card .label {
  font-size: 14px;
  color: #9ca3af;
  margin-top: 8px;
}

.monitor-main {
  display: grid;
  grid-template-columns: 250px 1fr 350px;
  gap: 20px;
}

.control-panel {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 12px;
  padding: 20px;
}

.control-group {
  margin-bottom: 16px;
}

.control-group label {
  display: block;
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 8px;
}

.control-group input,
.control-group select {
  width: 100%;
  padding: 8px;
  border: 1px solid #374151;
  border-radius: 6px;
  background: #1f2937;
  color: white;
}

.speed-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.speed-btn {
  flex: 1;
  min-width: 60px;
  padding: 8px;
  border: 1px solid #374151;
  border-radius: 6px;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  text-align: center;
  font-size: 12px;
}

.speed-btn.active {
  background: #667eea;
  border-color: #667eea;
  color: white;
}

.speed-btn small {
  display: block;
  font-size: 10px;
}

.anomaly-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #374151;
}

.buildings-section {
  background: transparent;
}

.buildings-section h3 {
  margin-bottom: 16px;
}

.buildings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.building-card {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 10px;
  padding: 14px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.building-card.normal { border-color: #4ade80; }
.building-card.warning { border-color: #fbbf24; }
.building-card.critical { 
  border-color: #f87171;
  animation: alert-pulse 1s infinite;
}

.building-card .name {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 6px;
}

.status-badge {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  display: inline-block;
}

.status-badge.normal { background: rgba(74, 222, 128, 0.2); color: #4ade80; }
.status-badge.warning { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
.status-badge.critical { background: rgba(248, 113, 113, 0.2); color: #f87171; }

.building-card .data {
  margin-top: 10px;
  font-size: 11px;
  color: #9ca3af;
}

.building-card .data div {
  display: flex;
  justify-content: space-between;
}

.alerts-panel {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 12px;
  padding: 20px;
  max-height: calc(100vh - 280px);
  overflow-y: auto;
}

.alerts-panel h3 {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.alert-count {
  background: #f87171;
  color: white;
  padding: 4px 10px;
  border-radius: 10px;
  font-size: 14px;
}

.btn-clear {
  background: transparent;
  border: 1px solid #4b5563;
  color: #9ca3af;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  margin-left: auto;
}

.btn-clear:hover {
  background: #ef4444;
  color: white;
}

.no-alerts {
  color: #6b7280;
  text-align: center;
  padding: 40px;
}

.alert-item {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
  border-left: 4px solid;
}

.alert-item.critical { border-color: #f87171; }
.alert-item.warning { border-color: #fbbf24; }
.alert-item.simulated { border-color: #a855f7; }

.alert-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 13px;
}

.alert-message {
  font-size: 12px;
  color: #d1d5db;
}
</style>