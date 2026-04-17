<template>
  <div class="anomaly">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>异常检测</span>
        </div>
      </template>
      
      <el-form :model="anomalyForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="建筑ID">
              <el-select
                v-model="anomalyForm.building_id"
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
            <el-form-item label="异常阈值">
              <el-input-number v-model="anomalyForm.threshold" :min="1" :max="10" :step="0.5" />
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item>
              <el-button type="primary" :loading="loading" @click="detectAnomalies">
                <el-icon><Warning /></el-icon>
                开始检测
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始时间">
              <el-date-picker
                v-model="anomalyForm.start_time"
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
                v-model="anomalyForm.end_time"
                type="datetime"
                placeholder="选择结束时间"
                format="YYYY-MM-DD HH:mm:ss"
                value-format="YYYY-MM-DD HH:mm:ss"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>
    
    <el-card style="margin-top: 20px;" v-if="anomalies.length > 0">
      <template #header>
        <div class="card-header">
          <span>检测结果 (共 {{ anomalies.length }} 个异常)</span>
        </div>
      </template>
      
      <el-table :data="anomalies" stripe border max-height="500">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="timestamp" label="时间" width="180" />
        <el-table-column prop="metric" label="指标" width="150" />
        <el-table-column prop="value" label="数值" width="120">
          <template #default="{ row }">
            {{ row.value?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="mean" label="平均值" width="120">
          <template #default="{ row }">
            {{ row.mean?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="std" label="标准差" width="120">
          <template #default="{ row }">
            {{ row.std?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="z_score" label="Z分数" width="100">
          <template #default="{ row }">
            <el-tag :type="Math.abs(row.z_score) > 3 ? 'danger' : 'warning'">
              {{ row.z_score?.toFixed(2) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.type === 'statistical_outlier' ? 'danger' : 'warning'">
              {{ row.type === 'statistical_outlier' ? '统计异常' : '系统异常' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="analyzeAnomaly(row)">
              分析
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog v-model="analysisDialogVisible" title="异常分析" width="60%">
      <div v-if="anomalyAnalysis">
        <el-descriptions title="可能原因" :column="1" border>
          <el-descriptions-item v-for="(cause, index) in anomalyAnalysis.analysis?.possible_causes" :key="index">
            {{ cause }}
          </el-descriptions-item>
        </el-descriptions>
        
        <el-divider />
        
        <el-descriptions title="建议措施" :column="1" border style="margin-top: 20px;">
          <el-descriptions-item v-for="(rec, index) in anomalyAnalysis.analysis?.recommendations" :key="index">
            {{ rec }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAppStore } from '@/store'
import { dataAPI, queryAPI, intelligenceAPI } from '@/api'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()

const buildings = ref([])
const loading = ref(false)
const anomalies = ref([])
const analysisDialogVisible = ref(false)
const anomalyAnalysis = ref(null)

const anomalyForm = ref({
  building_id: '',
  threshold: 3.0,
  start_time: '',
  end_time: ''
})

const loadBuildings = async () => {
  try {
    const res = await dataAPI.getBuildings()
    buildings.value = res.data.buildings
  } catch (error) {
    console.error('加载建筑列表失败:', error)
  }
}

const detectAnomalies = async () => {
  loading.value = true
  
  try {
    const params = {
      threshold: anomalyForm.value.threshold
    }
    
    if (anomalyForm.value.building_id) {
      params.building_id = anomalyForm.value.building_id
    }
    if (anomalyForm.value.start_time) {
      params.start_time = anomalyForm.value.start_time
    }
    if (anomalyForm.value.end_time) {
      params.end_time = anomalyForm.value.end_time
    }
    
    const res = await queryAPI.detectAnomalies(params)
    anomalies.value = res.data.anomalies || []
    
    ElMessage.success(`检测完成，发现 ${res.data.total_anomalies} 个异常`)
  } catch (error) {
    console.error('检测失败:', error)
    ElMessage.error('检测失败')
  } finally {
    loading.value = false
  }
}

const analyzeAnomaly = async (anomaly) => {
  try {
    const res = await intelligenceAPI.analyzeAnomaly({
      building_id: anomalyForm.value.building_id || 'Unknown',
      anomaly_data: {
        type: anomaly.type,
        metric: anomaly.metric,
        value: anomaly.value
      }
    })
    
    anomalyAnalysis.value = res.data
    analysisDialogVisible.value = true
  } catch (error) {
    console.error('分析失败:', error)
    ElMessage.error('分析失败')
  }
}

onMounted(() => {
  loadBuildings()
})
</script>

<style scoped>
.anomaly {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
</style>
