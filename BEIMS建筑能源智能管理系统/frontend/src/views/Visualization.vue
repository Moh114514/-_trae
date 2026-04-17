<template>
  <div class="visualization">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>可视化图表</span>
        </div>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="6">
          <el-select v-model="chartType" placeholder="选择图表类型">
            <el-option label="折线图" value="line" />
            <el-option label="柱状图" value="bar" />
            <el-option label="饼图" value="pie" />
            <el-option label="散点图" value="scatter" />
            <el-option label="面积图" value="area" />
            <el-option label="热力图" value="heatmap" />
            <el-option label="雷达图" value="radar" />
            <el-option label="仪表盘" value="gauge" />
          </el-select>
        </el-col>
        
        <el-col :span="6">
          <el-select v-model="selectedBuilding" placeholder="选择建筑" clearable>
            <el-option
              v-for="building in buildings"
              :key="building.building_id"
              :label="building.building_id"
              :value="building.building_id"
            />
          </el-select>
        </el-col>
        
        <el-col :span="6">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-col>
        
        <el-col :span="6">
          <el-button type="primary" :loading="loading" @click="generateChart">
            生成图表
          </el-button>
        </el-col>
      </el-row>
    </el-card>
    
    <el-card style="margin-top: 20px;">
      <div ref="chartContainer" class="chart-container"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'
import { useAppStore } from '@/store'
import { dataAPI, queryAPI, visualizationAPI } from '@/api'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()

const buildings = ref([])
const chartType = ref('line')
const selectedBuilding = ref('')
const dateRange = ref([])
const loading = ref(false)

const chartContainer = ref(null)
let chartInstance = null

const loadBuildings = async () => {
  try {
    const res = await dataAPI.getBuildings()
    buildings.value = res.data.buildings
  } catch (error) {
    console.error('加载建筑列表失败:', error)
  }
}

const generateChart = async () => {
  loading.value = true
  
  try {
    if (!chartInstance) {
      chartInstance = echarts.init(chartContainer.value)
    }
    
    let chartData = []
    let xField = 'timestamp'
    let yField = 'electricity_kwh'
    
    const params = {
      building_id: selectedBuilding.value
    }
    
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_time = dateRange.value[0] + ' 00:00:00'
      params.end_time = dateRange.value[1] + ' 23:59:59'
    }
    
    const aggregationRes = await queryAPI.timeAggregation({
      ...params,
      period: 'day'
    })
    
    if (aggregationRes.data.data) {
      chartData = aggregationRes.data.data.map(item => ({
        timestamp: item.timestamp,
        electricity_kwh: item.electricity_kwh,
        water_m3: item.water_m3,
        hvac_kwh: item.hvac_kwh
      }))
    }
    
    let option = {}
    
    switch (chartType.value) {
      case 'line':
        option = {
          title: { text: '能耗趋势图' },
          tooltip: { trigger: 'axis' },
          legend: { data: ['电力消耗', 'HVAC能耗', '用水量'] },
          xAxis: {
            type: 'category',
            data: chartData.map(d => d.timestamp)
          },
          yAxis: { type: 'value' },
          series: [
            {
              name: '电力消耗',
              type: 'line',
              data: chartData.map(d => d.electricity_kwh),
              smooth: true
            },
            {
              name: 'HVAC能耗',
              type: 'line',
              data: chartData.map(d => d.hvac_kwh),
              smooth: true
            },
            {
              name: '用水量',
              type: 'line',
              data: chartData.map(d => d.water_m3),
              smooth: true
            }
          ]
        }
        break
        
      case 'bar':
        option = {
          title: { text: '能耗柱状图' },
          tooltip: { trigger: 'axis' },
          xAxis: {
            type: 'category',
            data: chartData.map(d => d.timestamp)
          },
          yAxis: { type: 'value' },
          series: [{
            name: '电力消耗',
            type: 'bar',
            data: chartData.map(d => d.electricity_kwh)
          }]
        }
        break
        
      case 'pie':
        const pieData = [
          { name: 'HVAC系统', value: chartData.reduce((sum, d) => sum + (d.hvac_kwh || 0), 0) },
          { name: '其他用电', value: chartData.reduce((sum, d) => sum + (d.electricity_kwh || 0) - (d.hvac_kwh || 0), 0) }
        ]
        option = {
          title: { text: '能耗分布' },
          tooltip: { trigger: 'item' },
          series: [{
            type: 'pie',
            radius: '50%',
            data: pieData,
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }]
        }
        break
        
      case 'scatter':
        option = {
          title: { text: '能耗散点图' },
          tooltip: { trigger: 'item' },
          xAxis: { name: '电力消耗(kWh)' },
          yAxis: { name: 'HVAC能耗(kWh)' },
          series: [{
            type: 'scatter',
            data: chartData.map(d => [d.electricity_kwh, d.hvac_kwh])
          }]
        }
        break
        
      case 'area':
        option = {
          title: { text: '能耗面积图' },
          tooltip: { trigger: 'axis' },
          xAxis: {
            type: 'category',
            data: chartData.map(d => d.timestamp)
          },
          yAxis: { type: 'value' },
          series: [{
            name: '电力消耗',
            type: 'line',
            data: chartData.map(d => d.electricity_kwh),
            areaStyle: {}
          }]
        }
        break
        
      case 'radar':
        const avgElectricity = chartData.reduce((sum, d) => sum + (d.electricity_kwh || 0), 0) / chartData.length
        const avgHvac = chartData.reduce((sum, d) => sum + (d.hvac_kwh || 0), 0) / chartData.length
        const avgWater = chartData.reduce((sum, d) => sum + (d.water_m3 || 0), 0) / chartData.length
        
        option = {
          title: { text: '能耗雷达图' },
          radar: {
            indicator: [
              { name: '电力消耗', max: avgElectricity * 2 },
              { name: 'HVAC能耗', max: avgHvac * 2 },
              { name: '用水量', max: avgWater * 2 }
            ]
          },
          series: [{
            type: 'radar',
            data: [{
              value: [avgElectricity, avgHvac, avgWater],
              name: '平均能耗'
            }]
          }]
        }
        break
        
      case 'gauge':
        const totalElectricity = chartData.reduce((sum, d) => sum + (d.electricity_kwh || 0), 0)
        const maxElectricity = totalElectricity * 1.5
        option = {
          series: [{
            type: 'gauge',
            detail: { formatter: '{value}' },
            data: [{
              value: (totalElectricity / maxElectricity * 100).toFixed(2),
              name: '能耗利用率'
            }]
          }]
        }
        break
        
      default:
        option = {
          title: { text: '能耗趋势图' },
          tooltip: { trigger: 'axis' },
          xAxis: {
            type: 'category',
            data: chartData.map(d => d.timestamp)
          },
          yAxis: { type: 'value' },
          series: [{
            name: '电力消耗',
            type: 'line',
            data: chartData.map(d => d.electricity_kwh)
          }]
        }
    }
    
    chartInstance.setOption(option)
    ElMessage.success('图表生成成功')
  } catch (error) {
    console.error('生成图表失败:', error)
    ElMessage.error('生成图表失败')
  } finally {
    loading.value = false
  }
}

const handleResize = () => {
  chartInstance?.resize()
}

onMounted(() => {
  loadBuildings()
  window.addEventListener('resize', handleResize)
})
</script>

<style scoped>
.visualization {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.chart-container {
  width: 100%;
  height: 500px;
}
</style>
