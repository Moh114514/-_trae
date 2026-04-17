<template>
  <div class="data-import">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据导入</span>
        </div>
      </template>
      
      <el-tabs v-model="activeTab">
        <el-tab-pane label="CSV文件导入" name="csv">
          <el-upload
            ref="csvUpload"
            class="upload-area"
            drag
            action="#"
            :auto-upload="false"
            :limit="1"
            accept=".csv"
            :on-change="handleCSVChange"
            :on-exceed="handleExceed"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将CSV文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                只能上传CSV文件，且文件大小不超过100MB
              </div>
            </template>
          </el-upload>
          
          <el-button
            type="primary"
            :loading="importing"
            @click="importCSV"
            style="margin-top: 20px;"
          >
            开始导入
          </el-button>
        </el-tab-pane>
        
        <el-tab-pane label="Excel文件导入" name="excel">
          <el-upload
            ref="excelUpload"
            class="upload-area"
            drag
            action="#"
            :auto-upload="false"
            :limit="1"
            accept=".xlsx,.xls"
            :on-change="handleExcelChange"
            :on-exceed="handleExceed"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将Excel文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                只能上传Excel文件(.xlsx, .xls)，且文件大小不超过100MB
              </div>
            </template>
          </el-upload>
          
          <el-button
            type="primary"
            :loading="importing"
            @click="importExcel"
            style="margin-top: 20px;"
          >
            开始导入
          </el-button>
        </el-tab-pane>
      </el-tabs>
      
      <el-divider />
      
      <div class="import-result" v-if="importResult">
        <el-alert
          :title="importResult.success ? '导入成功' : '导入失败'"
          :type="importResult.success ? 'success' : 'error'"
          :description="importResult.message"
          show-icon
          :closable="false"
        />
        
        <div v-if="importResult.success" style="margin-top: 20px;">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="导入记录数">
              {{ importResult.records_imported }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
        
        <div v-if="importResult.errors && importResult.errors.length > 0" style="margin-top: 20px;">
          <el-alert
            title="错误信息"
            type="warning"
            :closable="false"
          >
            <ul>
              <li v-for="(error, index) in importResult.errors" :key="index">
                {{ error }}
              </li>
            </ul>
          </el-alert>
        </div>
      </div>
    </el-card>
    
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>数据格式说明</span>
        </div>
      </template>
      
      <el-descriptions :column="1" border>
        <el-descriptions-item label="Building_ID">建筑ID（必填）</el-descriptions-item>
        <el-descriptions-item label="Building_Type">建筑类型</el-descriptions-item>
        <el-descriptions-item label="Timestamp">时间戳（必填，格式：YYYY/MM/DD HH:MM）</el-descriptions-item>
        <el-descriptions-item label="Electricity_Consumption_kWh">电力消耗(kWh)</el-descriptions-item>
        <el-descriptions-item label="Water_Consumption_m3">用水量(m³)</el-descriptions-item>
        <el-descriptions-item label="HVAC_Energy_kWh">HVAC能耗(kWh)</el-descriptions-item>
        <el-descriptions-item label="CHW_Supply_Temp_C">冷冻水供水温度(°C)</el-descriptions-item>
        <el-descriptions-item label="CHW_Return_Temp_C">冷冻水回水温度(°C)</el-descriptions-item>
        <el-descriptions-item label="Outdoor_Temp_C">室外温度(°C)</el-descriptions-item>
        <el-descriptions-item label="Relative_Humidity_Pct">相对湿度(%)</el-descriptions-item>
        <el-descriptions-item label="Occupancy_Density_People_100qm">人员密度(人/100m²)</el-descriptions-item>
        <el-descriptions-item label="Meter_ID">仪表ID</el-descriptions-item>
        <el-descriptions-item label="System_Status">系统状态</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { dataAPI } from '@/api'
import { ElMessage } from 'element-plus'

const activeTab = ref('csv')
const importing = ref(false)
const importResult = ref(null)

const csvUpload = ref(null)
const excelUpload = ref(null)

let csvFile = null
let excelFile = null

const handleCSVChange = (file) => {
  csvFile = file.raw
}

const handleExcelChange = (file) => {
  excelFile = file.raw
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

const importCSV = async () => {
  if (!csvFile) {
    ElMessage.warning('请先选择CSV文件')
    return
  }
  
  importing.value = true
  importResult.value = null
  
  try {
    const formData = new FormData()
    formData.append('file', csvFile)
    
    const res = await dataAPI.importCSV(formData)
    importResult.value = res.data
    
    if (res.data.success) {
      ElMessage.success('数据导入成功')
    }
  } catch (error) {
    importResult.value = {
      success: false,
      message: error.response?.data?.detail || '导入失败',
      errors: []
    }
  } finally {
    importing.value = false
  }
}

const importExcel = async () => {
  if (!excelFile) {
    ElMessage.warning('请先选择Excel文件')
    return
  }
  
  importing.value = true
  importResult.value = null
  
  try {
    const formData = new FormData()
    formData.append('file', excelFile)
    
    const res = await dataAPI.importExcel(formData)
    importResult.value = res.data
    
    if (res.data.success) {
      ElMessage.success('数据导入成功')
    }
  } catch (error) {
    importResult.value = {
      success: false,
      message: error.response?.data?.detail || '导入失败',
      errors: []
    }
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.data-import {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.upload-area {
  width: 100%;
}

.import-result {
  margin-top: 20px;
}
</style>
