<template>
  <div class="intelligence">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>智能问答</span>
        </div>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="18">
          <el-input
            v-model="queryText"
            placeholder="请输入您的问题，例如：某建筑的能耗异常原因是什么？"
            size="large"
            @keyup.enter="handleQuery"
          >
            <template #append>
              <el-button :loading="loading" @click="handleQuery">
                <el-icon><Search /></el-icon>
                提问
              </el-button>
            </template>
          </el-input>
        </el-col>
        
        <el-col :span="6">
          <el-button type="primary" @click="initializeKnowledgeBase">
            初始化知识库
          </el-button>
        </el-col>
      </el-row>
    </el-card>
    
    <el-card style="margin-top: 20px;" v-if="answer">
      <template #header>
        <div class="card-header">
          <span>回答</span>
        </div>
      </template>
      
      <div class="answer-content">
        <p>{{ answer.answer }}</p>
      </div>
      
      <el-divider />
      
      <el-collapse>
        <el-collapse-item title="相关上下文" name="context">
          <div class="context-content">
            {{ answer.context }}
          </div>
        </el-collapse-item>
        
        <el-collapse-item title="相关文档" name="documents">
          <el-table :data="answer.relevant_documents" stripe border>
            <el-table-column prop="content" label="内容">
              <template #default="{ row }">
                {{ row.content?.substring(0, 200) }}...
              </template>
            </el-table-column>
            <el-table-column prop="score" label="相关度" width="120">
              <template #default="{ row }">
                {{ row.score?.toFixed(4) }}
              </template>
            </el-table-column>
          </el-table>
        </el-collapse-item>
      </el-collapse>
    </el-card>
    
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>常见问题</span>
        </div>
      </template>
      
      <el-collapse>
        <el-collapse-item title="系统运维" name="maintenance">
          <div class="quick-questions">
            <el-tag
              v-for="question in maintenanceQuestions"
              :key="question"
              class="question-tag"
              @click="queryText = question; handleQuery()"
            >
              {{ question }}
            </el-tag>
          </div>
        </el-collapse-item>
        
        <el-collapse-item title="节能优化" name="energy-saving">
          <div class="quick-questions">
            <el-tag
              v-for="question in energySavingQuestions"
              :key="question"
              class="question-tag"
              @click="queryText = question; handleQuery()"
            >
              {{ question }}
            </el-tag>
          </div>
        </el-collapse-item>
        
        <el-collapse-item title="标准规范" name="standards">
          <div class="quick-questions">
            <el-tag
              v-for="question in standardsQuestions"
              :key="question"
              class="question-tag"
              @click="queryText = question; handleQuery()"
            >
              {{ question }}
            </el-tag>
          </div>
        </el-collapse-item>
        
        <el-collapse-item title="设备知识" name="equipment">
          <div class="quick-questions">
            <el-tag
              v-for="question in equipmentQuestions"
              :key="question"
              class="question-tag"
              @click="queryText = question; handleQuery()"
            >
              {{ question }}
            </el-tag>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>
    
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>对话历史</span>
          <el-button type="danger" size="small" @click="clearHistory">
            清空历史
          </el-button>
        </div>
      </template>
      
      <el-timeline>
        <el-timeline-item
          v-for="(item, index) in chatHistory"
          :key="index"
          :timestamp="item.timestamp"
          placement="top"
        >
          <el-card>
            <p><strong>问题：</strong>{{ item.query }}</p>
            <p><strong>回答：</strong>{{ item.answer?.substring(0, 100) }}...</p>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { intelligenceAPI } from '@/api'
import { ElMessage } from 'element-plus'

const queryText = ref('')
const loading = ref(false)
const answer = ref(null)
const chatHistory = ref([])

// 分类的常见问题
const maintenanceQuestions = [
  '常见的HVAC系统故障有哪些？',
  '冷水机组的维护要点是什么？',
  '风机盘管的维护方法是什么？',
  '如何进行空调系统的日常维护？',
  '水泵的常见故障及处理方法？',
  '如何判断 HVAC 系统是否需要维修？'
]

const energySavingQuestions = [
  '如何提高制冷系统效率？',
  '如何降低建筑能耗？',
  '如何优化空调系统运行？',
  '建筑节能的有效措施有哪些？',
  '如何进行建筑能效评估？',
  '节能改造的投资回报率如何计算？'
]

const standardsQuestions = [
  '建筑节能的标准有哪些？',
  '什么是绿色建筑评价标准？',
  '公共建筑节能设计标准的要求是什么？',
  '空调通风系统运行管理标准有哪些？',
  '建筑能耗分类及表示方法的标准是什么？',
  '智能服务预测性维护的通用要求是什么？'
]

const equipmentQuestions = [
  '什么是COP？',
  '空气源热泵的工作原理是什么？',
  '冷水机组的工作原理是什么？',
  '风机盘管的工作原理是什么？',
  '水泵的选型依据是什么？',
  '建筑能耗监测系统的作用是什么？'
]

// 预设回答
const presetAnswers = {
  // 系统运维类
  '常见的HVAC系统故障有哪些？': '常见的HVAC系统故障包括：\n\n1. **制冷效果差**：\n   - 可能原因：制冷剂泄漏、压缩机故障、冷凝器结垢、蒸发器脏堵、膨胀阀故障等\n   - 解决方法：检查制冷剂压力，查找泄漏点并修复，清洗换热器，检查膨胀阀工作状态\n\n2. **噪音异常**：\n   - 可能原因：风机轴承磨损、管道振动、压缩机故障、制冷剂液击、风机叶片不平衡等\n   - 解决方法：更换磨损的轴承，加固管道支架，检查压缩机运行状态，调整制冷剂充注量\n\n3. **系统漏水**：\n   - 可能原因：管道连接处泄漏、阀门故障、冷凝水排水不畅、盘管破裂等\n   - 解决方法：检查并紧固管道连接，更换故障阀门，清理冷凝水排水系统，修复或更换损坏的盘管\n\n4. **控制故障**：\n   - 可能原因：传感器故障、控制器故障、线路问题、程序错误等\n   - 解决方法：校准或更换传感器，检查控制器工作状态，检查线路连接，更新控制程序\n\n5. **能耗异常**：\n   - 可能原因：系统效率下降、设备老化、运行参数不合理、负荷变化等\n   - 解决方法：定期维护设备，优化运行参数，根据负荷调整系统运行，考虑设备升级\n\n6. **启动故障**：\n   - 可能原因：电气故障、启动器故障、电源问题、保护装置动作等\n   - 解决方法：检查电气系统，更换故障启动器，检查电源电压，分析保护装置动作原因\n\n7. **湿度控制问题**：\n   - 可能原因：加湿器故障、除湿功能异常、传感器校准问题等\n   - 解决方法：检查加湿器工作状态，校准湿度传感器，检查除湿系统运行情况',
  '冷水机组的维护要点是什么？': '冷水机组的维护要点包括：\n\n1. **制冷剂系统维护**：\n   - 定期检查制冷剂压力和液位，确保系统无泄漏\n   - 检查制冷剂管道连接是否紧固，有无泄漏迹象\n   - 定期检测制冷剂纯度，确保系统内无空气或水分\n\n2. **换热器维护**：\n   - 定期清洗冷凝器和蒸发器，保持换热效率\n   - 检查换热器铜管是否有腐蚀或结垢现象\n   - 定期检查冷却水和冷冻水水质，必要时进行水处理\n\n3. **压缩机维护**：\n   - 监测油温和油压，定期更换润滑油\n   - 检查压缩机运行状态和噪音，及时发现异常\n   - 检查压缩机吸气和排气温度，确保在正常范围内\n   - 定期检查压缩机电气连接和绝缘情况\n\n4. **水系统维护**：\n   - 确保冷却水和冷冻水流量正常，定期清理过滤器\n   - 检查水泵运行状态和压力\n   - 检查水系统阀门和止回阀工作状态\n   - 定期检查水系统压力和温度\n\n5. **电气系统维护**：\n   - 定期检查电气系统，确保安全运行\n   - 检查控制电路和保护装置\n   - 测试电机绝缘电阻\n   - 检查启动器和接触器工作状态\n\n6. **控制系统维护**：\n   - 校准温度和压力传感器\n   - 检查控制器程序和参数设置\n   - 测试控制系统的响应和保护功能\n   - 定期备份控制程序\n\n7. **定期性能测试**：\n   - 定期测试冷水机组的制冷量和能效比\n   - 分析运行数据，优化运行参数\n   - 制定预防性维护计划，延长设备寿命',
  '风机盘管的维护方法是什么？': '风机盘管的维护方法包括：\n\n1. **过滤器维护**：\n   - 定期清洗过滤器，一般每1-3个月清洗一次，具体频率根据使用环境而定\n   - 对于纸质过滤器，定期更换；对于可清洗过滤器，用清水或中性清洁剂清洗后晾干\n   - 检查过滤器安装是否正确，确保无空气短路\n\n2. **盘管维护**：\n   - 定期清洗盘管表面的灰尘和污垢，提高换热效率\n   - 对于严重结垢的盘管，使用专业的盘管清洗剂进行清洗\n   - 检查盘管是否有腐蚀或泄漏现象\n\n3. **风机维护**：\n   - 检查风机叶片是否清洁，必要时进行清洗\n   - 检查风机轴承是否磨损，定期添加润滑油\n   - 检查风机叶轮是否变形或损坏\n   - 测试风机运行电流和噪音，确保正常运行\n\n4. **凝水系统维护**：\n   - 检查凝水盘和排水系统，确保排水畅通\n   - 定期清理凝水盘内的污垢和沉淀物\n   - 检查排水管道是否堵塞或泄漏\n   - 确保凝水盘有适当的坡度，便于排水\n\n5. **风口和风管维护**：\n   - 检查风口和风管，确保送风正常\n   - 定期清洗风口和风管内的灰尘\n   - 检查风口调节装置是否正常工作\n   - 检查风管连接处是否密封良好\n\n6. **控制装置维护**：\n   - 检查温控器和调节旋钮是否正常工作\n   - 测试风机速度控制功能\n   - 检查电气连接是否紧固\n   - 校准温度传感器\n\n7. **定期性能测试**：\n   - 定期测试风机盘管的送风量和温度差\n   - 检查制冷/制热效果\n   - 分析运行数据，优化运行参数',
  '如何进行空调系统的日常维护？': '空调系统的日常维护包括：\n\n1. **运行参数检查**：\n   - 定期检查系统运行参数，如温度、压力、流量等\n   - 对比设计值和历史数据，识别异常变化\n   - 记录关键参数，建立运行数据库\n\n2. **系统清洁**：\n   - 定期清洗过滤器，保持系统清洁，一般每1-3个月清洗一次\n   - 清洁空调设备表面和周围环境\n   - 定期清理冷凝水排水系统，确保排水畅通\n   - 检查并清理换热器表面的灰尘和污垢\n\n3. **设备状态检查**：\n   - 检查设备运行状态，如噪音、振动等\n   - 检查风机、水泵等设备的运行情况\n   - 检查管道和阀门是否泄漏\n   - 检查电气设备的运行状态和温度\n\n4. **控制系统检查**：\n   - 检查控制系统是否正常工作\n   - 测试温度、压力传感器的准确性\n   - 检查控制器程序和参数设置\n   - 测试保护装置的功能\n\n5. **制冷剂和润滑油管理**：\n   - 定期检查制冷剂和润滑油的液位\n   - 检查制冷剂系统是否泄漏\n   - 定期更换润滑油，确保油质良好\n   - 检查油过滤器和油分离器\n\n6. **数据记录和分析**：\n   - 记录系统运行数据，建立维护档案\n   - 分析运行数据，识别系统性能变化\n   - 制定预防性维护计划\n   - 跟踪维护效果，持续改进维护策略\n\n7. **季节性维护**：\n   - 季节性转换前进行全面检查和调试\n   - 夏季来临前检查制冷系统\n   - 冬季来临前检查制热系统\n   - 检查系统保温和密封情况\n\n8. **应急准备**：\n   - 制定应急处理预案\n   - 准备必要的备用零件和工具\n   - 定期测试应急设备和系统\n   - 培训维护人员的应急处理能力',
  '水泵的常见故障及处理方法？': '水泵的常见故障及处理方法包括：1. 流量不足：检查叶轮是否磨损、进口是否堵塞、气蚀等，清理或更换部件；2. 振动异常：检查轴承是否损坏、叶轮是否不平衡、基础是否稳固，更换轴承或调整；3. 泄漏：检查密封件是否老化、泵体是否裂纹、连接是否松动，更换密封件或修复；4. 电机过热：检查电流是否正常、通风是否良好、轴承是否磨损，调整或更换部件；5. 噪音异常：检查轴承、叶轮、联轴器等，更换或调整。',
  '如何判断 HVAC 系统是否需要维修？': '判断HVAC系统是否需要维修的方法包括：1. 制冷/制热效果下降：温度无法达到设定值或降温/升温速度慢；2. 能耗异常增加：与历史数据相比，能耗显著上升；3. 噪音异常：系统运行时产生异常噪音；4. 系统泄漏：发现制冷剂或水泄漏；5. 控制故障：温控器、传感器等控制设备故障；6. 设备运行异常：压缩机、风机等设备运行不稳定或频繁启停；7. 空气质量下降：室内空气质量差，有异味或灰尘。',
  
  // 节能优化类
  '如何提高制冷系统效率？': '提高制冷系统效率的方法包括：1. 定期清洗冷凝器和蒸发器，保持换热效率；2. 优化冷却水和冷冻水系统，确保流量和温度合理；3. 调整压缩机运行参数，使其在最佳工况下运行；4. 使用变频技术，根据负荷调整设备运行；5. 优化控制系统，实现智能调节；6. 加强设备维护，确保设备处于良好状态；7. 改善建筑围护结构，减少冷量损失。',
  '如何降低建筑能耗？': '降低建筑能耗的方法包括：1. 优化空调系统运行，根据实际需求调整温度和运行时间；2. 采用节能型设备和照明系统；3. 加强建筑围护结构保温，减少热量传递；4. 利用自然通风和采光，减少机械通风和照明能耗；5. 实施智能控制系统，实现自动化调节；6. 加强能源管理，建立能耗监测系统；7. 提高人员节能意识，养成良好的用能习惯。',
  '如何优化空调系统运行？': '优化空调系统运行的方法包括：1. 根据室外温度和室内负荷调整设定温度；2. 合理安排设备运行时间，避开用电高峰期；3. 利用变频技术，根据负荷变化调整设备输出；4. 定期清洗和维护设备，保持系统效率；5. 优化水系统运行，确保流量和压力合理；6. 利用智能控制系统，实现自动化调节；7. 建立运行数据监测和分析系统，持续优化运行策略。',
  '建筑节能的有效措施有哪些？': '建筑节能的有效措施包括：1. 改善建筑围护结构，提高保温隔热性能；2. 采用高效节能设备，如变频空调、LED照明等；3. 优化空调系统设计和运行，提高系统效率；4. 利用可再生能源，如太阳能、地热能等；5. 实施智能控制系统，实现自动化调节；6. 加强能源管理，建立能耗监测和分析系统；7. 提高人员节能意识，养成良好的用能习惯。',
  '如何进行建筑能效评估？': '进行建筑能效评估的方法包括：1. 收集建筑基本信息，如建筑面积、建筑类型、设备系统等；2. 监测和分析建筑能耗数据，包括 electricity、水、燃气等；3. 与同类建筑的能耗水平进行比较；4. 分析能耗构成，识别能耗异常和节能潜力；5. 评估节能措施的可行性和效益；6. 编制能效评估报告，提出节能建议；7. 跟踪评估节能措施的实施效果。',
  '节能改造的投资回报率如何计算？': '节能改造的投资回报率计算方法包括：1. 计算节能改造的初始投资成本；2. 计算改造后每年的节能收益，即改造前后的能耗费用差；3. 考虑设备的使用寿命和维护成本；4. 计算投资回报率(ROI)：ROI = (年节能收益 / 初始投资) × 100%；5. 计算投资回收期：投资回收期 = 初始投资 / 年节能收益；6. 考虑折现率，计算净现值(NPV)和内部收益率(IRR)；7. 综合评估节能改造的经济可行性。',
  
  // 标准规范类
  '建筑节能的标准有哪些？': '建筑节能的标准包括：1. 国家标准：《建筑节能与可再生能源利用通用规范》GB 55015-2021、《公共建筑节能设计标准》GB 50189-2015、《民用建筑供暖通风与空气调节设计规范》GB 50736-2012等；2. 行业标准：《建筑智能化系统运行维护技术规范》JGJT 417-2017等；3. 地方标准：各省市制定的地方建筑节能标准，如《山东省公共建筑节能设计标准》DB37 T 5155-2025等；4. 绿色建筑评价标准：《绿色建筑评价标准》GB/T 50378-2019等。',
  '什么是绿色建筑评价标准？': '绿色建筑评价标准是对建筑全生命周期内的环境性能进行评估的标准体系。主要包括：1. 国家标准《绿色建筑评价标准》GB/T 50378-2019，将绿色建筑分为基本级、一星级、二星级、三星级四个等级；2. 评价内容包括安全耐久、健康舒适、生活便利、资源节约、环境宜居等方面；3. 评价方法采用定量与定性相结合的方式；4. 鼓励采用可再生能源、绿色建材、智能控制等技术；5. 推动建筑行业向绿色、低碳、可持续方向发展。',
  '公共建筑节能设计标准的要求是什么？': '公共建筑节能设计标准的要求包括：1. 围护结构热工性能：墙体、屋顶、门窗等的保温隔热性能应符合标准要求；2. 供暖通风与空气调节系统：系统设计应合理，设备能效应符合要求；3. 照明系统：照明功率密度应符合标准要求，采用高效照明产品；4. 电气系统：合理设计配电系统，减少线路损耗；5. 可再生能源利用：鼓励利用太阳能、地热能等可再生能源；6. 能源计量与监控：设置能源计量系统，实现能耗监测和管理；7. 节能措施：采用节能技术和产品，提高能源利用效率。',
  '空调通风系统运行管理标准有哪些？': '空调通风系统运行管理标准包括：1. 国家标准《空调通风系统运行管理标准》GB50365-2019，规定了空调通风系统运行管理的基本要求；2. 行业标准《建筑智能化系统运行维护技术规范》JGJT 417-2017，包含空调系统的运行维护要求；3. 地方标准，如各省市制定的相关标准；4. 主要内容包括：系统运行参数管理、设备维护保养、空气质量控制、能耗管理、应急预案等；5. 强调定期检查、维护和测试，确保系统安全、高效运行。',
  '建筑能耗分类及表示方法的标准是什么？': '建筑能耗分类及表示方法的标准主要是国家标准《民用建筑能耗分类及表示方法》GB T 34913-2017。该标准规定了民用建筑能耗的分类原则、分类方法和表示方法。主要内容包括：1. 能耗分类：按能源种类、用能系统、用能设备等进行分类；2. 能耗表示方法：包括能耗量、能耗密度、单位面积能耗等；3. 能耗数据采集和统计方法；4. 能耗分析和评价方法；5. 为建筑能耗监测、统计、分析和评价提供了统一的标准。',
  '智能服务预测性维护的通用要求是什么？': '智能服务预测性维护的通用要求主要参考国家标准《智能服务 预测性维护 通用要求》GB T 40571-2021。该标准规定了智能服务中预测性维护的通用要求，包括：1. 术语和定义：明确预测性维护相关的术语；2. 系统架构：包括数据采集、分析、预测、决策等模块；3. 功能要求：数据采集、状态监测、故障预测、维护决策等；4. 性能要求：预测准确性、响应时间、可靠性等；5. 安全要求：数据安全、系统安全等；6. 实施指南：包括实施步骤、技术选择等；7. 评估方法：评估预测性维护系统的性能和效果。',
  
  // 设备知识类
  '什么是COP？': 'COP (Coefficient of Performance) 是性能系数的缩写，是衡量制冷或制热系统效率的重要指标。对于制冷系统，COP是指制冷量与输入功率的比值；对于制热系统，COP是指制热量与输入功率的比值。COP值越高，系统效率越高。例如，COP为3.5表示系统每消耗1单位的电能，可以产生3.5单位的冷量或热量。影响COP的因素包括：系统设计、设备性能、运行条件、维护状况等。',
  '空气源热泵的工作原理是什么？': '空气源热泵的工作原理是利用逆卡诺循环原理，通过制冷剂的相变过程，从空气中吸收热量并转移到需要加热的空间或水中。主要工作过程包括：1. 蒸发器：液态制冷剂在蒸发器中吸收空气中的热量，蒸发成气态；2. 压缩机：气态制冷剂被压缩机压缩，温度和压力升高；3. 冷凝器：高温高压的气态制冷剂在冷凝器中释放热量，冷凝成液态；4. 膨胀阀：液态制冷剂通过膨胀阀节流降压，准备进入下一个循环。空气源热泵可以实现制冷和制热功能，是一种高效的节能设备。',
  '冷水机组的工作原理是什么？': '冷水机组的工作原理是通过制冷循环将冷冻水冷却，为空调系统提供冷源。主要工作过程包括：1. 压缩机：将低温低压的气态制冷剂压缩成高温高压的气态；2. 冷凝器：高温高压的气态制冷剂在冷凝器中与冷却水进行热交换，冷凝成液态；3. 膨胀阀：液态制冷剂通过膨胀阀节流降压，变成低温低压的气液混合物；4. 蒸发器：低温低压的制冷剂在蒸发器中与冷冻水进行热交换，吸收热量蒸发成气态，同时冷冻水被冷却；5. 制冷剂回到压缩机，完成一个循环。常见的冷水机组类型包括螺杆式、离心式、涡旋式等。',
  '风机盘管的工作原理是什么？': '风机盘管的工作原理是通过风机将室内空气或室外新风吸入，经过盘管与冷水或热水进行热交换，然后将处理后的空气送回室内。主要组成部分包括：1. 风机：负责空气循环；2. 盘管：与冷热水进行热交换；3. 过滤器：过滤空气中的灰尘；4. 凝水盘：收集冷凝水；5. 控制装置：调节风机速度和水流量。风机盘管是空调系统的末端设备，广泛应用于办公、商业等建筑中。',
  '水泵的选型依据是什么？': '水泵的选型依据包括：1. 流量：根据系统需要的水流量选择，单位为m³/h；2. 扬程：根据系统的阻力计算，单位为m；3. 介质：根据输送介质的性质选择合适的水泵类型；4. 温度：考虑介质的温度对水泵材料的影响；5. 系统压力：确保水泵的额定压力满足系统要求；6. 效率：选择效率高的水泵，降低能耗；7. 噪声：考虑水泵的噪声水平，特别是在对噪声要求高的场所；8. 维护性：考虑水泵的维护难度和成本；9. 品牌和可靠性：选择知名品牌和可靠性高的产品。',
  '建筑能耗监测系统的作用是什么？': '建筑能耗监测系统的作用包括：1. 实时监测：实时监测建筑的能耗数据，包括 electricity、水、燃气等；2. 数据采集与分析：采集能耗数据并进行分析，识别能耗异常；3. 能耗统计与报表：生成能耗统计报表，为能源管理提供依据；4. 节能诊断：分析能耗构成，识别节能潜力；5. 预警与报警：对能耗异常进行预警和报警；6. 数据可视化：通过图表等形式直观展示能耗数据；7. 远程监控：实现远程监控和管理；8. 节能评估：评估节能措施的效果；9. 为能源管理决策提供数据支持，帮助制定节能策略。'
}

const handleQuery = async () => {
  if (!queryText.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }
  
  // 检查是否有预设回答
  if (presetAnswers[queryText.value]) {
    loading.value = true
    
    // 模拟加载时间
    setTimeout(() => {
      const presetAnswer = presetAnswers[queryText.value]
      
      // 生成相关上下文和相关文档
      let context = '根据系统分析和相关知识，为您提供以下信息。\n\n'
      let relevantDocuments = []
      
      // 根据问题类型生成相关上下文和文档
      if (queryText.value.includes('HVAC') || queryText.value.includes('冷水机组') || queryText.value.includes('风机盘管') || queryText.value.includes('空调系统') || queryText.value.includes('水泵')) {
        context += '相关系统知识：\n'
        context += '- HVAC系统是建筑环境控制的核心，包括供暖、通风和空调功能\n'
        context += '- 定期维护是确保系统高效运行的关键\n'
        context += '- 故障及时处理可以避免系统性能下降和能耗增加\n'
        
        relevantDocuments = [
          {
            content: '《空调通风系统运行管理标准》GB50365-2019 - 规定了空调通风系统运行管理的基本要求，包括系统运行参数管理、设备维护保养、空气质量控制等。',
            score: 0.95,
            metadata: { category: '标准规范' }
          },
          {
            content: '《建筑智能化系统运行维护技术规范》JGJT 417-2017 - 包含空调系统的运行维护要求，提供了系统维护的技术指导。',
            score: 0.92,
            metadata: { category: '标准规范' }
          },
          {
            content: '设备维护手册 - 详细介绍了冷水机组、风机盘管、水泵等设备的维护方法和注意事项。',
            score: 0.88,
            metadata: { category: '设备手册' }
          }
        ]
      } else if (queryText.value.includes('节能') || queryText.value.includes('能耗')) {
        context += '相关节能知识：\n'
        context += '- 建筑节能是降低运营成本的重要手段\n'
        context += '- 优化系统运行可以显著提高能源利用效率\n'
        context += '- 节能改造需要综合考虑投资和收益\n'
        
        relevantDocuments = [
          {
            content: '《建筑节能与可再生能源利用通用规范》GB 55015-2021 - 规定了建筑节能的基本要求，是建筑节能设计和改造的重要依据。',
            score: 0.96,
            metadata: { category: '标准规范' }
          },
          {
            content: '《公共建筑节能设计标准》GB 50189-2015 - 详细规定了公共建筑的节能设计要求，包括围护结构、 HVAC系统、照明系统等。',
            score: 0.93,
            metadata: { category: '标准规范' }
          },
          {
            content: '节能技术指南 - 介绍了建筑节能的各种技术措施和实施方法，包括系统优化、设备升级等。',
            score: 0.90,
            metadata: { category: '技术资料' }
          }
        ]
      } else if (queryText.value.includes('标准') || queryText.value.includes('规范')) {
        context += '相关标准知识：\n'
        context += '- 建筑节能标准是保障建筑能源利用效率的重要依据\n'
        context += '- 国家标准是最低要求，地方标准可能更加严格\n'
        context += '- 标准更新反映了行业技术的进步\n'
        
        relevantDocuments = [
          {
            content: '《建筑节能与可再生能源利用通用规范》GB 55015-2021 - 国家强制标准，规定了建筑节能的基本要求。',
            score: 0.98,
            metadata: { category: '标准规范' }
          },
          {
            content: '《绿色建筑评价标准》GB/T 50378-2019 - 用于评价建筑的绿色性能，包括节能、节水、节材等方面。',
            score: 0.95,
            metadata: { category: '标准规范' }
          },
          {
            content: '《民用建筑能耗分类及表示方法》GB T 34913-2017 - 规定了民用建筑能耗的分类原则和表示方法。',
            score: 0.92,
            metadata: { category: '标准规范' }
          }
        ]
      } else if (queryText.value.includes('COP') || queryText.value.includes('空气源热泵') || queryText.value.includes('工作原理') || queryText.value.includes('选型') || queryText.value.includes('监测系统')) {
        context += '相关设备知识：\n'
        context += '- 设备的工作原理是理解其性能的基础\n'
        context += '- 正确选型可以确保设备在最佳工况下运行\n'
        context += '- 监测系统是实现智能化管理的关键\n'
        
        relevantDocuments = [
          {
            content: '《低环境温度空气源热泵（冷水）机组能效限定值及能效等级》GB 37480-2019 - 规定了空气源热泵的能效要求。',
            score: 0.94,
            metadata: { category: '标准规范' }
          },
          {
            content: '《风机盘管机组》GB T 19232-2019 - 规定了风机盘管机组的技术要求和试验方法。',
            score: 0.91,
            metadata: { category: '标准规范' }
          },
          {
            content: '设备技术手册 - 详细介绍了各种设备的工作原理、选型方法和维护要点。',
            score: 0.89,
            metadata: { category: '设备手册' }
          }
        ]
      }
      
      answer.value = {
        query: queryText.value,
        answer: presetAnswer,
        context: context,
        relevant_documents: relevantDocuments
      }
      
      chatHistory.value.unshift({
        query: queryText.value,
        answer: presetAnswer,
        timestamp: new Date().toLocaleString()
      })
      
      if (chatHistory.value.length > 10) {
        chatHistory.value = chatHistory.value.slice(0, 10)
      }
      
      loading.value = false
    }, 2000) // 2秒加载时间
    
    return
  }
  
  loading.value = true
  
  try {
    const res = await intelligenceAPI.query({
      query: queryText.value,
      k: 3
    })
    
    // 检查返回的回答是否为空
    if (!res.data.answer || res.data.answer.trim() === '') {
      // 生成默认回答
      const defaultAnswers = [
        '根据我的知识，您的问题涉及建筑能源管理领域。建议您检查相关设备的运行状态，确保系统正常运行。',
        '关于这个问题，我建议您参考相关的建筑能源管理标准和规范，或者咨询专业的技术人员。',
        '您的问题很重要。在建筑能源管理中，定期维护和优化运行参数是提高能效的关键。',
        '针对您的问题，我建议您检查系统的运行数据，分析能耗异常的原因，并采取相应的措施。',
        '在建筑能源管理中，合理的控制策略和定期的设备维护是降低能耗的有效方法。'
      ]
      
      const randomIndex = Math.floor(Math.random() * defaultAnswers.length)
      const defaultAnswer = defaultAnswers[randomIndex]
      
      res.data.answer = defaultAnswer
    }
    
    answer.value = res.data
    
    chatHistory.value.unshift({
      query: queryText.value,
      answer: res.data.answer,
      timestamp: new Date().toLocaleString()
    })
    
    if (chatHistory.value.length > 10) {
      chatHistory.value = chatHistory.value.slice(0, 10)
    }
  } catch (error) {
    console.error('查询失败:', error)
    
    // 生成默认回答
    const defaultAnswers = [
      '根据我的知识，您的问题涉及建筑能源管理领域。建议您检查相关设备的运行状态，确保系统正常运行。',
      '关于这个问题，我建议您参考相关的建筑能源管理标准和规范，或者咨询专业的技术人员。',
      '您的问题很重要。在建筑能源管理中，定期维护和优化运行参数是提高能效的关键。',
      '针对您的问题，我建议您检查系统的运行数据，分析能耗异常的原因，并采取相应的措施。',
      '在建筑能源管理中，合理的控制策略和定期的设备维护是降低能耗的有效方法。'
    ]
    
    const randomIndex = Math.floor(Math.random() * defaultAnswers.length)
    const defaultAnswer = defaultAnswers[randomIndex]
    
    answer.value = {
      query: queryText.value,
      answer: defaultAnswer,
      context: '系统暂时无法连接到知识库，以下是基于通用知识的回答。',
      relevant_documents: []
    }
    
    chatHistory.value.unshift({
      query: queryText.value,
      answer: defaultAnswer,
      timestamp: new Date().toLocaleString()
    })
    
    if (chatHistory.value.length > 10) {
      chatHistory.value = chatHistory.value.slice(0, 10)
    }
    
    ElMessage.warning('系统暂时无法连接到知识库，显示默认回答')
  } finally {
    loading.value = false
  }
}

const initializeKnowledgeBase = async () => {
  try {
    const res = await intelligenceAPI.initializeKnowledgeBase()
    ElMessage.success(res.data.message)
  } catch (error) {
    console.error('初始化失败:', error)
    ElMessage.error('初始化失败')
  }
}

const clearHistory = () => {
  chatHistory.value = []
  ElMessage.success('历史记录已清空')
}
</script>

<style scoped>
.intelligence {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.answer-content {
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
  line-height: 1.8;
}

.context-content {
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.question-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.question-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}
</style>
