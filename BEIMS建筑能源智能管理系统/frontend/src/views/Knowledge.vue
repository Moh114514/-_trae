<template>
  <div class="knowledge">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>知识库管理</span>
        </div>
      </template>
      
      <el-tabs v-model="activeTab">
        <el-tab-pane label="数据字典" name="dictionary">
          <el-table :data="dataDictionary" stripe border>
            <el-table-column prop="name" label="名称" width="150" />
            <el-table-column prop="unit" label="单位" width="100" />
            <el-table-column prop="description" label="描述" />
            <el-table-column prop="normal_range" label="正常范围" width="200" />
            <el-table-column prop="anomaly_threshold" label="异常阈值" width="200" />
          </el-table>
        </el-tab-pane>
        
        <el-tab-pane label="设备手册" name="manuals">
          <el-collapse>
            <el-collapse-item
              v-for="(manual, key) in equipmentManuals"
              :key="key"
              :title="manual.name"
              :name="key"
            >
              <el-descriptions :column="1" border>
                <el-descriptions-item label="描述">
                  {{ manual.description }}
                </el-descriptions-item>
                <el-descriptions-item label="工作原理">
                  {{ manual.operation_principles }}
                </el-descriptions-item>
                <el-descriptions-item label="常见问题">
                  <ul>
                    <li v-for="(issue, index) in manual.common_issues" :key="index">
                      {{ issue }}
                    </li>
                  </ul>
                </el-descriptions-item>
                <el-descriptions-item label="维护建议">
                  <ul>
                    <li v-for="(tip, index) in manual.maintenance_tips" :key="index">
                      {{ tip }}
                    </li>
                  </ul>
                </el-descriptions-item>
              </el-descriptions>
            </el-collapse-item>
          </el-collapse>
        </el-tab-pane>
        
        <el-tab-pane label="标准规范" name="standards">
          <el-collapse>
            <el-collapse-item title="国家标准" name="national">
              <el-list>
                <el-list-item v-for="(standard, index) in nationalStandards" :key="index">
                  <div class="standard-item">
                    <div class="standard-title">{{ standard.title }}</div>
                    <div class="standard-code">{{ standard.code }}</div>
                    <div class="standard-description">{{ standard.description }}</div>
                  </div>
                </el-list-item>
              </el-list>
            </el-collapse-item>
            
            <el-collapse-item title="行业标准" name="industry">
              <el-list>
                <el-list-item v-for="(standard, index) in industryStandards" :key="index">
                  <div class="standard-item">
                    <div class="standard-title">{{ standard.title }}</div>
                    <div class="standard-code">{{ standard.code }}</div>
                    <div class="standard-description">{{ standard.description }}</div>
                  </div>
                </el-list-item>
              </el-list>
            </el-collapse-item>
            
            <el-collapse-item title="地方标准" name="local">
              <el-list>
                <el-list-item v-for="(standard, index) in localStandards" :key="index">
                  <div class="standard-item">
                    <div class="standard-title">{{ standard.title }}</div>
                    <div class="standard-code">{{ standard.code }}</div>
                    <div class="standard-description">{{ standard.description }}</div>
                  </div>
                </el-list-item>
              </el-list>
            </el-collapse-item>
          </el-collapse>
        </el-tab-pane>
        
        <el-tab-pane label="故障案例" name="cases">
          <el-table :data="faultCases" stripe border>
            <el-table-column prop="title" label="故障名称" width="200" />
            <el-table-column prop="equipment" label="设备类型" width="150" />
            <el-table-column prop="symptom" label="故障症状" />
            <el-table-column prop="cause" label="故障原因" />
            <el-table-column prop="solution" label="解决方案" />
          </el-table>
        </el-tab-pane>
        
        <el-tab-pane label="添加文档" name="add">
          <el-form :model="addForm" label-width="100px">
            <el-form-item label="文档类型">
              <el-radio-group v-model="addForm.type">
                <el-radio label="file">文件上传</el-radio>
                <el-radio label="text">文本输入</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item v-if="addForm.type === 'file'" label="上传文件">
              <el-upload
                ref="uploadRef"
                action="#"
                :auto-upload="false"
                :limit="1"
                :on-change="handleFileChange"
              >
                <el-button type="primary">选择文件</el-button>
                <template #tip>
                  <div class="el-upload__tip">
                    支持 PDF、TXT 格式文件
                  </div>
                </template>
              </el-upload>
            </el-form-item>
            
            <el-form-item v-else label="文本内容">
              <el-input
                v-model="addForm.text"
                type="textarea"
                :rows="10"
                placeholder="请输入文本内容"
              />
            </el-form-item>
            
            <el-form-item label="文档类别">
              <el-select v-model="addForm.category" placeholder="选择文档类别">
                <el-option label="设备手册" value="设备手册" />
                <el-option label="标准规范" value="标准规范" />
                <el-option label="故障案例" value="故障案例" />
                <el-option label="技术资料" value="技术资料" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="标签">
              <el-input v-model="addForm.tags" placeholder="多个标签用逗号分隔" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" :loading="adding" @click="addDocument">
                添加到知识库
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="搜索知识" name="search">
          <el-input
            v-model="searchQuery"
            placeholder="输入关键词搜索知识库"
            @keyup.enter="searchKnowledge"
          >
            <template #append>
              <el-button :loading="searching" @click="searchKnowledge">
                搜索
              </el-button>
            </template>
          </el-input>
          
          <div v-if="searchResults.length > 0" style="margin-top: 20px;">
            <el-card
              v-for="(result, index) in searchResults"
              :key="index"
              style="margin-bottom: 10px;"
            >
              <div class="search-result">
                <div class="result-content">{{ result.content }}</div>
                <div class="result-meta">
                  <el-tag>相关度: {{ result.score?.toFixed(4) }}</el-tag>
                  <el-tag type="info" style="margin-left: 10px;">
                    {{ result.metadata?.category || '未分类' }}
                  </el-tag>
                </div>
              </div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { intelligenceAPI } from '@/api'
import { ElMessage } from 'element-plus'

const activeTab = ref('dictionary')
const dataDictionary = ref([])
const equipmentManuals = ref({})

// 标准规范数据
const nationalStandards = ref([
  {
    title: '风机盘管机组',
    code: 'GB T 19232-2019',
    description: '规定了风机盘管机组的分类、技术要求、试验方法、检验规则及标志、包装、运输和贮存等内容。'
  },
  {
    title: '低环境温度空气源热泵（冷水）机组能效限定值及能效等级',
    code: 'GB 37480-2019',
    description: '规定了低环境温度空气源热泵（冷水）机组的能效限定值、能效等级、测试方法和检验规则。'
  },
  {
    title: '供暖通风与空气调节术语标准',
    code: 'GB T 50155-2015',
    description: '规定了供暖通风与空气调节工程中常用的术语及其定义。'
  },
  {
    title: '建筑节能基本术语标准',
    code: 'GB T 51140-2015',
    description: '规定了建筑节能领域的基本术语及其定义。'
  },
  {
    title: '智能服务 预测性维护 通用要求',
    code: 'GB T 40571-2021',
    description: '规定了智能服务中预测性维护的通用要求，包括术语和定义、系统架构、功能要求、性能要求等。'
  }
])

const industryStandards = ref([
  {
    title: '建筑智能化系统运行维护技术规范',
    code: 'JGJT 417-2017',
    description: '规定了建筑智能化系统运行维护的技术要求，包括系统运行、维护、管理等内容。'
  }
])

const localStandards = ref([
  {
    title: '低温空气源热泵供暖（空调）系统技术规程',
    code: 'DB37 T 5095-2017',
    description: '规定了山东省低温空气源热泵供暖（空调）系统的设计、安装、调试、运行和维护等技术要求。'
  },
  {
    title: '公共建筑节能监测系统技术标准',
    code: 'DB37 T 5197-2021',
    description: '规定了山东省公共建筑节能监测系统的设计、施工、验收和运行管理等技术要求。'
  },
  {
    title: '公共建筑节能设计标准',
    code: 'DB37 T 5155-2025',
    description: '规定了山东省公共建筑节能设计的技术要求，包括建筑与围护结构、供暖通风与空气调节、给水排水、电气等系统的节能设计。'
  }
])

// 故障案例数据
const faultCases = ref([
  {
    title: '冷水机组不制冷',
    equipment: '冷水机组',
    symptom: '机组运行但无冷量输出',
    cause: '制冷剂泄漏、压缩机故障、膨胀阀故障',
    solution: '检查制冷剂泄漏点并修复，更换故障部件'
  },
  {
    title: '风机盘管噪音大',
    equipment: '风机盘管',
    symptom: '运行时产生异常噪音',
    cause: '风机叶片积尘、轴承磨损、电机故障',
    solution: '清洁风机叶片，更换磨损轴承，检修电机'
  },
  {
    title: '水泵不启动',
    equipment: '水泵',
    symptom: '水泵通电但不运转',
    cause: '电源故障、电机烧坏、叶轮卡死',
    solution: '检查电源，更换电机，清理叶轮'
  },
  {
    title: '空调系统能耗异常',
    equipment: '空调系统',
    symptom: '能耗显著高于正常水平',
    cause: '系统泄漏、设备老化、运行参数不合理',
    solution: '检查系统泄漏，更换老化设备，优化运行参数'
  },
  {
    title: '空气源热泵制热效果差',
    equipment: '空气源热泵',
    symptom: '冬季制热效果不佳',
    cause: '制冷剂不足、室外机结霜、压缩机效率下降',
    solution: '补充制冷剂，检查除霜系统，检修压缩机'
  }
])

const addForm = ref({
  type: 'file',
  text: '',
  category: '',
  tags: ''
})

const adding = ref(false)
const searching = ref(false)
const searchQuery = ref('')
const searchResults = ref([])
const uploadRef = ref(null)
let selectedFile = null

const loadDataDictionary = async () => {
  try {
    const res = await intelligenceAPI.getDataDictionary()
    const dict = res.data
    
    dataDictionary.value = Object.keys(dict).map(key => ({
      key,
      ...dict[key]
    }))
  } catch (error) {
    console.error('加载数据字典失败:', error)
    // 添加默认数据
    dataDictionary.value = [
      {
        name: '冷水温度',
        unit: '°C',
        description: '冷水系统的供水温度',
        normal_range: '6-10°C',
        anomaly_threshold: '<5°C 或 >12°C'
      },
      {
        name: '冷却水温度',
        unit: '°C',
        description: '冷却水系统的供水温度',
        normal_range: '25-32°C',
        anomaly_threshold: '<20°C 或 >35°C'
      },
      {
        name: '空调负荷',
        unit: 'kW',
        description: '空调系统的冷负荷',
        normal_range: '根据建筑面积和使用情况而定',
        anomaly_threshold: '超出设计负荷的120%'
      },
      {
        name: 'COP',
        unit: '',
        description: '制冷系数，衡量空调系统效率',
        normal_range: '3.0-4.5',
        anomaly_threshold: '<2.5'
      },
      {
        name: '能耗强度',
        unit: 'kWh/m²',
        description: '单位面积能耗',
        normal_range: '50-150 kWh/m²·年',
        anomaly_threshold: '>200 kWh/m²·年'
      }
    ]
  }
}

const loadEquipmentManuals = async () => {
  try {
    const res = await intelligenceAPI.getEquipmentManuals()
    equipmentManuals.value = res.data
  } catch (error) {
    console.error('加载设备手册失败:', error)
    // 添加默认数据
    equipmentManuals.value = {
      '冷水机组': {
        name: '冷水机组',
        description: '冷水机组是中央空调系统的核心设备，用于制冷并提供冷水。',
        operation_principles: '冷水机组通过压缩机将制冷剂压缩成高温高压气体，然后通过冷凝器散热，变成高压液体，再通过膨胀阀节流降压，变成低温低压液体，最后在蒸发器中吸收热量，变成气体，完成制冷循环。',
        common_issues: [
          '制冷剂泄漏',
          '压缩机故障',
          '冷凝器结垢',
          '膨胀阀故障',
          '电气控制故障'
        ],
        maintenance_tips: [
          '定期检查制冷剂压力和液位',
          '定期清洗冷凝器和蒸发器',
          '定期更换润滑油',
          '检查电气系统和控制装置',
          '定期测试系统性能'
        ]
      },
      '风机盘管': {
        name: '风机盘管',
        description: '风机盘管是中央空调系统的末端设备，用于向室内输送冷/热风。',
        operation_principles: '风机盘管通过风机将室内空气或室外新风吸入，经过盘管与冷水或热水进行热交换，然后将处理后的空气送入室内。',
        common_issues: [
          '过滤器堵塞',
          '风机噪音大',
          '盘管结垢',
          '凝水盘漏水',
          '电机故障'
        ],
        maintenance_tips: [
          '定期清洗过滤器',
          '定期清洗盘管',
          '检查风机轴承并添加润滑油',
          '清理凝水盘和排水系统',
          '检查电气连接和控制装置'
        ]
      },
      '空气源热泵': {
        name: '空气源热泵',
        description: '空气源热泵是一种利用空气中的热量进行加热或制冷的设备。',
        operation_principles: '空气源热泵通过压缩机将制冷剂压缩成高温高压气体，然后通过冷凝器将热量释放到室内（制热模式）或室外（制冷模式），再通过膨胀阀节流降压，最后通过蒸发器吸收热量。',
        common_issues: [
          '制冷剂泄漏',
          '室外机结霜',
          '压缩机故障',
          '换热器脏堵',
          '控制系统故障'
        ],
        maintenance_tips: [
          '定期检查制冷剂压力',
          '定期清洗室外机换热器',
          '检查除霜系统',
          '检查电气系统和控制装置',
          '定期测试系统性能'
        ]
      },
      '水泵': {
        name: '水泵',
        description: '水泵是用于输送水的设备，在中央空调系统中用于循环冷水和冷却水。',
        operation_principles: '水泵通过电机驱动叶轮旋转，产生离心力，将水从吸入端输送到排出端。',
        common_issues: [
          '水泵不启动',
          '水泵噪音大',
          '水泵漏水',
          '水泵效率下降',
          '电机故障'
        ],
        maintenance_tips: [
          '定期检查水泵轴承并添加润滑油',
          '检查水泵密封件',
          '定期清理水泵滤网',
          '检查电气系统',
          '定期测试水泵性能'
        ]
      }
    }
  }
}

const handleFileChange = (file) => {
  selectedFile = file.raw
}

const addDocument = async () => {
  adding.value = true
  
  try {
    if (addForm.value.type === 'file') {
      if (!selectedFile) {
        ElMessage.warning('请选择文件')
        adding.value = false
        return
      }
      
      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('category', addForm.value.category)
      formData.append('tags', addForm.value.tags)
      
      await intelligenceAPI.addDocument(formData)
    } else {
      if (!addForm.value.text.trim()) {
        ElMessage.warning('请输入文本内容')
        adding.value = false
        return
      }
      
      await intelligenceAPI.addText({
        text: addForm.value.text,
        category: addForm.value.category,
        tags: addForm.value.tags
      })
    }
    
    ElMessage.success('添加成功')
    
    addForm.value = {
      type: 'file',
      text: '',
      category: '',
      tags: ''
    }
    selectedFile = null
  } catch (error) {
    console.error('添加失败:', error)
    ElMessage.error('添加失败')
  } finally {
    adding.value = false
  }
}

const searchKnowledge = async () => {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  
  searching.value = true
  
  try {
    const res = await intelligenceAPI.search({
      query: searchQuery.value,
      k: 5
    })
    
    searchResults.value = res.data.results
  } catch (error) {
    console.error('搜索失败:', error)
    ElMessage.error('搜索失败')
  } finally {
    searching.value = false
  }
}

onMounted(() => {
  loadDataDictionary()
  loadEquipmentManuals()
})
</script>

<style scoped>
.knowledge {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.search-result {
  padding: 10px;
}

.result-content {
  margin-bottom: 10px;
  line-height: 1.6;
}

.result-meta {
  display: flex;
  align-items: center;
}

.standard-item {
  padding: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.standard-title {
  font-weight: bold;
  margin-bottom: 5px;
  color: #303133;
}

.standard-code {
  color: #606266;
  margin-bottom: 5px;
  font-size: 14px;
}

.standard-description {
  color: #606266;
  line-height: 1.6;
  font-size: 14px;
}
</style>
