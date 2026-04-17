<template>
  <div class="query-data">
    <!-- 自然语言查询 -->
    <el-card style="margin-bottom: 20px;">
      <template #header>
        <div class="card-header">
          <span>自然语言查询</span>
        </div>
      </template>
      
      <el-form :model="naturalLanguageForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="20">
            <el-form-item label="查询语句">
              <el-input
                v-model="naturalLanguageForm.query"
                placeholder="例如：查询建筑Aral从2021-01-01到2021-01-31的电力消耗数据"
                clearable
              />
              <div class="text-xs text-gray-500 mt-1">
                支持的建筑ID: Aral, Baikal, Caspian, Erie, Huron, Ladoga, Malawi, Michigan, Ontario, Superior, Titicaca, Victoria, Vostok, Winnipeg
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item>
              <el-button type="primary" :loading="loading" @click="handleNaturalLanguageQuery" style="width: 100%;">
                <el-icon><ChatDotRound /></el-icon>
                智能查询
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row v-if="naturalLanguageResult.extracted_params" class="mt-2">
          <el-col :span="24">
            <el-card shadow="hover" class="bg-blue-50">
              <div class="text-sm">
                <p class="font-bold">解析结果：</p>
                <p v-for="(value, key) in naturalLanguageResult.extracted_params" :key="key" class="mb-1">
                  <span class="font-medium">{{ formatParamKey(key) }}:</span> {{ formatParamValue(key, value) }}
                </p>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <el-row v-if="tableData.length === 0 && naturalLanguageResult.extracted_params" class="mt-2">
          <el-col :span="24">
            <el-alert
              title="未找到数据"
              type="warning"
              :closable="false"
            >
              <div slot="default">
                <p>系统已解析您的查询，但未找到匹配的数据。可能的原因：</p>
                <ul class="list-disc pl-4">
                  <li>建筑ID不存在或格式不正确</li>
                  <li>时间范围超出数据范围</li>
                  <li>查询条件过于严格</li>
                </ul>
                <p class="mt-2">建议：</p>
                <ul class="list-disc pl-4">
                  <li>检查建筑ID是否正确（支持的建筑ID: Aral, Baikal, Caspian, Erie, Huron, Ladoga, Malawi, Michigan, Ontario, Superior, Titicaca, Victoria, Vostok, Winnipeg）</li>
                  <li>调整时间范围</li>
                  <li>尝试使用精准参数查询</li>
                </ul>
              </div>
            </el-alert>
          </el-col>
        </el-row>
      </el-form>
    </el-card>
    
    <!-- 传统精准查询 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>精准参数查询</span>
        </div>
      </template>
      
      <el-form :model="queryForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="建筑ID">
              <el-select
                v-model="queryForm.building_id"
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
          
          <el-col :span="8">
            <el-form-item label="建筑类型">
              <el-select
                v-model="queryForm.building_type"
                placeholder="请选择建筑类型"
                clearable
                filterable
              >
                <el-option label="办公楼" value="office" />
                <el-option label="商场" value="mall" />
                <el-option label="酒店" value="hotel" />
                <el-option label="医院" value="hospital" />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="仪表ID">
              <el-select
                v-model="queryForm.meter_id"
                placeholder="请选择仪表"
                clearable
                filterable
              >
                <el-option
                  v-for="meter in meters"
                  :key="meter.meter_id"
                  :label="meter.meter_id"
                  :value="meter.meter_id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="系统状态">
              <el-select v-model="queryForm.system_status" placeholder="请选择状态" clearable>
                <el-option label="正常" value="Normal" />
                <el-option label="异常" value="Abnormal" />
                <el-option label="维护" value="Maintenance" />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="16">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="开始时间">
                  <el-date-picker
                    v-model="queryForm.start_time"
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
                    v-model="queryForm.end_time"
                    type="datetime"
                    placeholder="选择结束时间"
                    format="YYYY-MM-DD HH:mm:ss"
                    value-format="YYYY-MM-DD HH:mm:ss"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-col>
        </el-row>
        
        <!-- 监测参数范围 -->
        <el-row :gutter="20" class="mt-2">
          <el-col :span="8">
            <el-form-item label="电力消耗(kWh)">
              <el-input-number v-model="queryForm.min_electricity" placeholder="最小值" :min="0" style="width: 48%; margin-right: 4%;" />
              <el-input-number v-model="queryForm.max_electricity" placeholder="最大值" :min="0" style="width: 48%;" />
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="用水量(m³)">
              <el-input-number v-model="queryForm.min_water" placeholder="最小值" :min="0" style="width: 48%; margin-right: 4%;" />
              <el-input-number v-model="queryForm.max_water" placeholder="最大值" :min="0" style="width: 48%;" />
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="HVAC能耗(kWh)">
              <el-input-number v-model="queryForm.min_hvac" placeholder="最小值" :min="0" style="width: 48%; margin-right: 4%;" />
              <el-input-number v-model="queryForm.max_hvac" placeholder="最大值" :min="0" style="width: 48%;" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20" class="mt-2">
          <el-col :span="8">
            <el-form-item label="室外温度(°C)">
              <el-input-number v-model="queryForm.min_temp" placeholder="最小值" style="width: 48%; margin-right: 4%;" />
              <el-input-number v-model="queryForm.max_temp" placeholder="最大值" style="width: 48%;" />
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="湿度(%)">
              <el-input-number v-model="queryForm.min_humidity" placeholder="最小值" :min="0" :max="100" style="width: 48%; margin-right: 4%;" />
              <el-input-number v-model="queryForm.max_humidity" placeholder="最大值" :min="0" :max="100" style="width: 48%;" />
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="人员密度">
              <el-input-number v-model="queryForm.occupancy_density" placeholder="人员密度" :min="0" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20" class="mt-2">
          <el-col :span="8">
            <el-form-item label="分页设置">
              <el-input-number v-model="queryForm.page" placeholder="页码" :min="1" style="width: 48%; margin-right: 4%;" />
              <el-input-number v-model="queryForm.page_size" placeholder="每页条数" :min="1" :max="1000" style="width: 48%;" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleQuery">
            <el-icon><Search /></el-icon>
            精准查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>查询结果 (共 {{ total }} 条)</span>
          <el-button type="primary" size="small" @click="exportData">
            <el-icon><Download /></el-icon>
            导出数据
          </el-button>
        </div>
      </template>
      
      <el-table
        :data="tableData"
        stripe
        border
        style="width: 100%"
        max-height="400"
        v-loading="loading"
      >
        <el-table-column prop="building_id" label="建筑ID" width="120" fixed />
        <el-table-column prop="building_type" label="建筑类型" width="120" />
        <el-table-column prop="timestamp" label="时间" width="180" />
        <el-table-column prop="electricity_kwh" label="电力消耗(kWh)" width="140">
          <template #default="{ row }">
            {{ row.electricity_kwh?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="water_m3" label="用水量(m³)" width="120">
          <template #default="{ row }">
            {{ row.water_m3?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="hvac_kwh" label="HVAC能耗(kWh)" width="140">
          <template #default="{ row }">
            {{ row.hvac_kwh?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="outdoor_temp" label="室外温度(°C)" width="120">
          <template #default="{ row }">
            {{ row.outdoor_temp?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="humidity_pct" label="湿度(%)" width="100">
          <template #default="{ row }">
            {{ row.humidity_pct?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="occupancy_density" label="人员密度" width="100">
          <template #default="{ row }">
            {{ row.occupancy_density?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="meter_id" label="仪表ID" width="150" />
        <el-table-column prop="system_status" label="系统状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.system_status === 'Normal' ? 'success' : 'danger'">
              {{ row.system_status }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container" style="margin-top: 20px; display: flex; justify-content: flex-end;">
        <el-pagination
          v-model:current-page="queryForm.page"
          v-model:page-size="queryForm.page_size"
          :page-sizes="[10, 20, 50, 100, 200, 500, 1000]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAppStore } from '@/store'
import { dataAPI, queryAPI } from '@/api'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()

const buildings = ref([])
const meters = ref([])
const loading = ref(false)
const tableData = ref([])
const total = ref(0)

// 自然语言查询表单
const naturalLanguageForm = ref({
  query: ''
})

// 自然语言查询结果
const naturalLanguageResult = ref({
  extracted_params: null
})

// 精准查询表单
const queryForm = ref({
  building_id: '',
  building_type: '',
  meter_id: '',
  system_status: '',
  start_time: '',
  end_time: '',
  min_electricity: null,
  max_electricity: null,
  min_water: null,
  max_water: null,
  min_hvac: null,
  max_hvac: null,
  min_temp: null,
  max_temp: null,
  min_humidity: null,
  max_humidity: null,
  occupancy_density: null,
  page: 1,
  page_size: 100
})

const loadBuildingsAndMeters = async () => {
  try {
    const [buildingsRes, metersRes] = await Promise.all([
      dataAPI.getBuildings(),
      dataAPI.getMeters()
    ])
    
    buildings.value = buildingsRes.data.buildings
    meters.value = metersRes.data.meters
    
    appStore.setBuildings(buildingsRes.data.buildings)
    appStore.setMeters(metersRes.data.meters)
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

const handleQuery = async () => {
  loading.value = true
  
  try {
    // 清空自然语言查询结果，确保分页时执行精准查询
    naturalLanguageResult.value = {}
    
    const params = {}
    
    // 复制所有非空参数
    for (const [key, value] of Object.entries(queryForm.value)) {
      if (value !== null && value !== '' && value !== undefined) {
        params[key] = value
      }
    }
    
    const res = await queryAPI.queryData(params)
    tableData.value = res.data.data
    total.value = res.data.total
    
    ElMessage.success(`查询成功，共 ${res.data.total} 条数据`)
  } catch (error) {
    console.error('查询失败:', error)
    ElMessage.error('查询失败，请检查参数')
  } finally {
    loading.value = false
  }
}

const handleNaturalLanguageQuery = async () => {
  if (!naturalLanguageForm.value.query.trim()) {
    ElMessage.warning('请输入查询语句')
    return
  }
  
  loading.value = true
  
  try {
    const res = await queryAPI.naturalLanguageQuery({
      query: naturalLanguageForm.value.query,
      page: queryForm.value.page,
      page_size: queryForm.value.page_size
    })
    
    tableData.value = res.data.data
    total.value = res.data.total
    naturalLanguageResult.value = res.data
    
    ElMessage.success(`智能查询成功，共 ${res.data.total} 条数据`)
  } catch (error) {
    console.error('智能查询失败:', error)
    ElMessage.error('智能查询失败，请检查查询语句')
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (size) => {
  queryForm.value.page_size = size
  // 重新执行当前查询
  if (naturalLanguageResult.value.extracted_params) {
    handleNaturalLanguageQuery()
  } else {
    handleQuery()
  }
}

const handleCurrentChange = (current) => {
  queryForm.value.page = current
  // 重新执行当前查询
  if (naturalLanguageResult.value.extracted_params) {
    handleNaturalLanguageQuery()
  } else {
    handleQuery()
  }
}

const handleReset = () => {
  queryForm.value = {
    building_id: '',
    building_type: '',
    meter_id: '',
    system_status: '',
    start_time: '',
    end_time: '',
    min_electricity: null,
    max_electricity: null,
    min_water: null,
    max_water: null,
    min_hvac: null,
    max_hvac: null,
    min_temp: null,
    max_temp: null,
    min_humidity: null,
    max_humidity: null,
    occupancy_density: null,
    page: 1,
    page_size: 100
  }
  tableData.value = []
  total.value = 0
  naturalLanguageForm.value.query = ''
  naturalLanguageResult.value = {
    extracted_params: null
  }
}

const exportData = () => {
  if (tableData.value.length === 0) {
    ElMessage.warning('没有数据可导出')
    return
  }
  
  const csvContent = [
    Object.keys(tableData.value[0]).join(','),
    ...tableData.value.map(row => Object.values(row).join(','))
  ].join('\n')
  
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `energy_data_${new Date().getTime()}.csv`
  link.click()
  
  ElMessage.success('数据导出成功')
}

// 格式化参数键
const formatParamKey = (key) => {
  const keyMap = {
    building_id: '建筑ID',
    building_type: '建筑类型',
    start_time: '开始时间',
    end_time: '结束时间',
    meter_id: '仪表ID',
    system_status: '系统状态',
    min_electricity: '最小电力消耗',
    max_electricity: '最大电力消耗',
    min_water: '最小用水量',
    max_water: '最大用水量',
    min_hvac: '最小HVAC能耗',
    max_hvac: '最大HVAC能耗',
    min_temp: '最小温度',
    max_temp: '最大温度',
    min_humidity: '最小湿度',
    max_humidity: '最大湿度',
    occupancy_density: '人员密度'
  }
  return keyMap[key] || key
}

// 格式化参数值
const formatParamValue = (key, value) => {
  if (value instanceof Date) {
    return value.toLocaleString()
  }
  return value
}

onMounted(() => {
  loadBuildingsAndMeters()
})
</script>

<style scoped>
.query-data {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
</style>
