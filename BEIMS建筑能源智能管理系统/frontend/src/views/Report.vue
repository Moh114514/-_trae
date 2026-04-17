<template>
  <div class="agent-report-page">
    <el-card class="control-card" shadow="never">
      <template #header>
        <div class="header-row">
          <div>
            <h2>智能体统计报表工作台</h2>
            <p>一键生成基础统计、分析诊断与决策支持报表</p>
          </div>
          <div class="header-actions">
            <el-button type="primary" :loading="loading" @click="generateReport">生成可视化报表</el-button>
            <el-button type="success" :disabled="!reportData" @click="exportHtmlReport">导出HTML报表</el-button>
          </div>
        </div>
      </template>

      <el-form :model="form" label-width="120px">
        <el-row :gutter="16">
          <el-col :xs="24" :md="12">
            <el-form-item label="聚焦建筑">
              <el-select v-model="form.building_id" placeholder="可选，默认全部" clearable filterable>
                <el-option
                  v-for="item in buildings"
                  :key="item.building_id"
                  :label="item.building_id"
                  :value="item.building_id"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-form-item label="对比建筑">
              <el-select v-model="form.building_ids" multiple clearable filterable placeholder="可多选，不选则自动取全部">
                <el-option
                  v-for="item in buildings"
                  :key="item.building_id"
                  :label="item.building_id"
                  :value="item.building_id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :xs="24" :md="12">
            <el-form-item label="开始时间">
              <el-date-picker
                v-model="form.start_time"
                type="datetime"
                value-format="YYYY-MM-DD HH:mm:ss"
                format="YYYY-MM-DD HH:mm:ss"
                placeholder="选择开始时间"
              />
            </el-form-item>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-form-item label="结束时间">
              <el-date-picker
                v-model="form.end_time"
                type="datetime"
                value-format="YYYY-MM-DD HH:mm:ss"
                format="YYYY-MM-DD HH:mm:ss"
                placeholder="选择结束时间"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :xs="24" :md="12">
            <el-form-item label="对比建筑上限">
              <el-input-number v-model="form.top_n" :min="1" :max="20" />
            </el-form-item>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-form-item label="碳排放因子">
              <el-input-number v-model="form.carbon_factor" :precision="3" :step="0.01" :min="0" :max="2" />
              <span class="unit-tip">kgCO2/kWh</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="快速区间">
          <el-button-group>
            <el-button @click="setQuickRange('q1')">2021 Q1</el-button>
            <el-button @click="setQuickRange('q2')">2021 Q2</el-button>
            <el-button @click="setQuickRange('summer')">2021 夏季</el-button>
            <el-button @click="setQuickRange('year')">2021 全年</el-button>
          </el-button-group>
        </el-form-item>
      </el-form>
    </el-card>

    <div v-if="reportData" class="report-content">
      <el-row :gutter="16" class="kpi-grid">
        <el-col :xs="12" :md="6">
          <el-card class="kpi-card" shadow="hover">
            <div class="kpi-label">总电耗</div>
            <div class="kpi-value">{{ fmt(reportData.kpis.total_electricity_kwh) }}</div>
            <div class="kpi-unit">kWh</div>
          </el-card>
        </el-col>

        <el-col :xs="12" :md="6">
          <el-card class="kpi-card" shadow="hover">
            <div class="kpi-label">平均COP</div>
            <div class="kpi-value">{{ fmt(reportData.kpis.average_cop, 3) }}</div>
            <div class="kpi-unit">效率指数</div>
          </el-card>
        </el-col>

        <el-col :xs="12" :md="6">
          <el-card class="kpi-card" shadow="hover">
            <div class="kpi-label">异常点数</div>
            <div class="kpi-value">{{ reportData.kpis.anomaly_count }}</div>
            <div class="kpi-unit">个</div>
          </el-card>
        </el-col>

        <el-col :xs="12" :md="6">
          <el-card class="kpi-card" shadow="hover">
            <div class="kpi-label">碳排放估算</div>
            <div class="kpi-value">{{ fmt(reportData.kpis.carbon_emission_ton, 3) }}</div>
            <div class="kpi-unit">吨CO2</div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16" class="chart-grid">
        <el-col :xs="24" :lg="12">
          <el-card shadow="never">
            <template #header>月度能耗统计</template>
            <div ref="monthlyChartRef" class="chart-box"></div>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="12">
          <el-card shadow="never">
            <template #header>分建筑能耗对比</template>
            <div ref="comparisonChartRef" class="chart-box"></div>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="12">
          <el-card shadow="never">
            <template #header>异常分布</template>
            <div ref="anomalyChartRef" class="chart-box"></div>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="12">
          <el-card shadow="never">
            <template #header>COP效率趋势</template>
            <div ref="copChartRef" class="chart-box"></div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16" class="analysis-grid">
        <el-col :xs="24" :lg="12">
          <el-card shadow="never">
            <template #header>简要分析结论</template>
            <p class="brief">{{ reportData.analysis.brief }}</p>
            <ul class="analysis-list">
              <li v-for="(item, idx) in reportData.analysis.conclusions" :key="`c-${idx}`">{{ item }}</li>
            </ul>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="12">
          <el-card shadow="never">
            <template #header>决策支持建议</template>
            <ul class="analysis-list">
              <li v-for="(item, idx) in reportData.analysis.recommendations" :key="`r-${idx}`">{{ item }}</li>
            </ul>
            <el-divider />
            <div class="decision-item">
              <span>潜在节能量:</span>
              <strong>{{ fmt(reportData.decision_support.energy_saving.potential_savings_kwh) }} kWh</strong>
            </div>
            <div class="decision-item">
              <span>潜在节能率:</span>
              <strong>{{ fmt(reportData.decision_support.energy_saving.potential_savings_pct, 2) }}%</strong>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { dataAPI, queryAPI } from '@/api'

const loading = ref(false)
const buildings = ref([])
const reportData = ref(null)
const route = useRoute()
const autoActionExecuted = ref(false)

const form = ref({
  building_id: '',
  building_ids: [],
  start_time: '2021-01-01 00:00:00',
  end_time: '2021-12-31 23:59:59',
  top_n: 8,
  carbon_factor: 0.785
})

const monthlyChartRef = ref(null)
const comparisonChartRef = ref(null)
const anomalyChartRef = ref(null)
const copChartRef = ref(null)

const chartInstances = {
  monthly: null,
  comparison: null,
  anomaly: null,
  cop: null
}

const fmt = (value, digits = 2) => {
  const n = Number(value)
  if (Number.isNaN(n)) return '0.00'
  return n.toFixed(digits)
}

const setQuickRange = (mode) => {
  if (mode === 'q1') {
    form.value.start_time = '2021-01-01 00:00:00'
    form.value.end_time = '2021-03-31 23:59:59'
  } else if (mode === 'q2') {
    form.value.start_time = '2021-04-01 00:00:00'
    form.value.end_time = '2021-06-30 23:59:59'
  } else if (mode === 'summer') {
    form.value.start_time = '2021-06-01 00:00:00'
    form.value.end_time = '2021-08-31 23:59:59'
  } else {
    form.value.start_time = '2021-01-01 00:00:00'
    form.value.end_time = '2021-12-31 23:59:59'
  }
}

const parseBooleanFlag = (value) => {
  const normalized = String(value || '').trim().toLowerCase()
  return normalized === '1' || normalized === 'true' || normalized === 'yes'
}

const applyQueryParamsToForm = () => {
  const query = route.query || {}

  if (typeof query.building_id === 'string') {
    form.value.building_id = query.building_id.trim()
  }

  if (typeof query.building_ids === 'string') {
    form.value.building_ids = query.building_ids
      .split(',')
      .map((item) => item.trim())
      .filter((item) => item)
  }

  if (typeof query.start_time === 'string') {
    form.value.start_time = query.start_time.trim()
  }

  if (typeof query.end_time === 'string') {
    form.value.end_time = query.end_time.trim()
  }

  if (typeof query.top_n === 'string') {
    const parsed = Number(query.top_n)
    if (!Number.isNaN(parsed) && parsed >= 1 && parsed <= 20) {
      form.value.top_n = parsed
    }
  }

  if (typeof query.carbon_factor === 'string') {
    const parsed = Number(query.carbon_factor)
    if (!Number.isNaN(parsed) && parsed >= 0 && parsed <= 2) {
      form.value.carbon_factor = parsed
    }
  }
}

const loadBuildings = async () => {
  try {
    const res = await dataAPI.getBuildings()
    buildings.value = res.data?.buildings || []
  } catch (error) {
    buildings.value = []
  }
}

const ensureChart = (key, domRef) => {
  if (!domRef?.value) return null
  if (chartInstances[key]) {
    chartInstances[key].dispose()
  }
  chartInstances[key] = echarts.init(domRef.value)
  return chartInstances[key]
}

const renderMonthlyChart = () => {
  const chart = ensureChart('monthly', monthlyChartRef)
  if (!chart) return

  const list = reportData.value?.charts?.monthly_energy || []
  const months = list.map((x) => x.month)

  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 40, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: months },
    yAxis: { type: 'value', name: 'kWh/m3' },
    series: [
      {
        name: '电耗(kWh)',
        type: 'line',
        smooth: true,
        data: list.map((x) => x.electricity_kwh)
      },
      {
        name: 'HVAC(kWh)',
        type: 'line',
        smooth: true,
        data: list.map((x) => x.hvac_kwh)
      },
      {
        name: '水耗(m3)',
        type: 'bar',
        yAxisIndex: 0,
        data: list.map((x) => x.water_m3)
      }
    ]
  })
}

const renderComparisonChart = () => {
  const chart = ensureChart('comparison', comparisonChartRef)
  if (!chart) return

  const list = reportData.value?.charts?.building_comparison || []

  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 20, bottom: 70 },
    xAxis: {
      type: 'category',
      axisLabel: { interval: 0, rotate: 30 },
      data: list.map((x) => x.building_id)
    },
    yAxis: { type: 'value', name: 'kWh' },
    series: [
      {
        name: '总电耗',
        type: 'bar',
        data: list.map((x) => x.total_electricity_kwh),
        itemStyle: { color: '#2d7ff9' }
      }
    ]
  })
}

const renderAnomalyChart = () => {
  const chart = ensureChart('anomaly', anomalyChartRef)
  if (!chart) return

  const byMetric = reportData.value?.charts?.anomaly_distribution?.by_metric || []
  const bySeverity = reportData.value?.charts?.anomaly_distribution?.by_severity || []

  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { top: 0 },
    series: [
      {
        name: '按指标',
        type: 'pie',
        radius: ['35%', '55%'],
        center: ['30%', '60%'],
        data: byMetric
      },
      {
        name: '按等级',
        type: 'pie',
        radius: ['35%', '55%'],
        center: ['75%', '60%'],
        data: bySeverity
      }
    ]
  })
}

const renderCopChart = () => {
  const chart = ensureChart('cop', copChartRef)
  if (!chart) return

  const list = reportData.value?.charts?.cop_trend || []
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: list.map((x) => x.month) },
    yAxis: { type: 'value', name: 'COP' },
    series: [
      {
        name: '月均COP',
        type: 'line',
        smooth: true,
        areaStyle: {},
        data: list.map((x) => x.avg_cop)
      }
    ]
  })
}

const renderAllCharts = () => {
  renderMonthlyChart()
  renderComparisonChart()
  renderAnomalyChart()
  renderCopChart()
}

const generateReport = async (options = {}) => {
  const { silentSuccess = false } = options
  loading.value = true
  try {
    const payload = {
      building_id: form.value.building_id || null,
      building_ids: form.value.building_ids.length ? form.value.building_ids : null,
      start_time: form.value.start_time || null,
      end_time: form.value.end_time || null,
      top_n: form.value.top_n,
      carbon_factor: form.value.carbon_factor
    }

    const res = await queryAPI.getAgentReport(payload)
    reportData.value = res.data

    await nextTick()
    renderAllCharts()
    if (!silentSuccess) {
      ElMessage.success('报表生成成功')
    }
  } catch (error) {
    console.error(error)
    ElMessage.error(error?.response?.data?.detail || '报表生成失败')
  } finally {
    loading.value = false
  }
}

const escapeHtml = (text) => {
  return String(text ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

const toSafeJSON = (value) => {
  return JSON.stringify(value).replace(/</g, '\\u003c')
}

const formatFileTimestamp = () => {
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`
}

const exportHtmlReport = (options = {}) => {
  const { silentSuccess = false } = options
  if (!reportData.value) {
    ElMessage.warning('请先生成报表再导出')
    return
  }

  const report = reportData.value
  const timeRange = report?.report_meta?.time_range || {}

  const monthlyList = report?.charts?.monthly_energy || []
  const comparisonList = report?.charts?.building_comparison || []
  const byMetric = report?.charts?.anomaly_distribution?.by_metric || []
  const bySeverity = report?.charts?.anomaly_distribution?.by_severity || []
  const copList = report?.charts?.cop_trend || []

  const monthlyOption = {
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 40, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: monthlyList.map((x) => x.month) },
    yAxis: { type: 'value', name: 'kWh/m3' },
    series: [
      {
        name: '电耗(kWh)',
        type: 'line',
        smooth: true,
        data: monthlyList.map((x) => x.electricity_kwh)
      },
      {
        name: 'HVAC(kWh)',
        type: 'line',
        smooth: true,
        data: monthlyList.map((x) => x.hvac_kwh)
      },
      {
        name: '水耗(m3)',
        type: 'bar',
        data: monthlyList.map((x) => x.water_m3)
      }
    ]
  }

  const comparisonOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 20, bottom: 70 },
    xAxis: {
      type: 'category',
      axisLabel: { interval: 0, rotate: 30 },
      data: comparisonList.map((x) => x.building_id)
    },
    yAxis: { type: 'value', name: 'kWh' },
    series: [
      {
        name: '总电耗',
        type: 'bar',
        data: comparisonList.map((x) => x.total_electricity_kwh),
        itemStyle: { color: '#2d7ff9' }
      }
    ]
  }

  const anomalyOption = {
    tooltip: { trigger: 'item' },
    legend: { top: 0 },
    series: [
      {
        name: '按指标',
        type: 'pie',
        radius: ['35%', '55%'],
        center: ['30%', '60%'],
        data: byMetric
      },
      {
        name: '按等级',
        type: 'pie',
        radius: ['35%', '55%'],
        center: ['75%', '60%'],
        data: bySeverity
      }
    ]
  }

  const copOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: copList.map((x) => x.month) },
    yAxis: { type: 'value', name: 'COP' },
    series: [
      {
        name: '月均COP',
        type: 'line',
        smooth: true,
        areaStyle: {},
        data: copList.map((x) => x.avg_cop)
      }
    ]
  }

  const generatedAt = new Date().toLocaleString('zh-CN')
  const reportTitle = `智能体统计报表_${formatFileTimestamp()}`

  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${escapeHtml(reportTitle)}</title>
  <style>
    body { margin: 0; font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: #f3f5f8; color: #0f172a; }
    .wrap { max-width: 1240px; margin: 20px auto; padding: 0 16px; }
    .panel { background: #fff; border-radius: 12px; box-shadow: 0 10px 25px rgba(2, 20, 43, 0.08); margin-bottom: 16px; overflow: hidden; }
    .panel-header { padding: 16px 20px; border-bottom: 1px solid #e5e7eb; }
    .panel-body { padding: 16px 20px; }
    h1 { margin: 0; font-size: 24px; }
    .meta { margin-top: 6px; color: #475569; font-size: 14px; }
    .meta-line { margin-top: 4px; color: #64748b; font-size: 13px; }
    .kpis { display: grid; grid-template-columns: repeat(4, minmax(180px, 1fr)); gap: 12px; }
    .kpi { background: #f8fafc; border-radius: 10px; padding: 12px; border: 1px solid #e2e8f0; }
    .kpi-label { color: #64748b; font-size: 13px; }
    .kpi-value { margin-top: 8px; font-size: 28px; font-weight: 700; color: #0b1220; }
    .kpi-unit { margin-top: 4px; color: #64748b; font-size: 12px; }
    .grid-2 { display: grid; grid-template-columns: repeat(2, minmax(320px, 1fr)); gap: 12px; }
    .chart-card { border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; background: #fff; }
    .chart-title { padding: 10px 12px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #334155; }
    .chart { height: 320px; }
    .analysis-grid { display: grid; grid-template-columns: repeat(2, minmax(320px, 1fr)); gap: 12px; }
    .list { margin: 0; padding-left: 20px; color: #1f2937; line-height: 1.8; }
    .brief { margin: 0 0 10px 0; color: #475569; }
    .row { display: flex; justify-content: space-between; margin: 6px 0; color: #334155; }
    @media (max-width: 900px) {
      .kpis, .grid-2, .analysis-grid { grid-template-columns: 1fr; }
      .chart { height: 280px; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="panel">
      <div class="panel-header">
        <h1>建筑能源智能体统计报表</h1>
        <div class="meta">导出时间：${escapeHtml(generatedAt)}</div>
        <div class="meta-line">统计范围：${escapeHtml(timeRange.start_time || '未设置')} ~ ${escapeHtml(timeRange.end_time || '未设置')}</div>
        <div class="meta-line">聚焦建筑：${escapeHtml(report?.report_meta?.focus_building || '全部')}</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">关键指标</div>
      <div class="panel-body">
        <div class="kpis">
          <div class="kpi"><div class="kpi-label">总电耗</div><div class="kpi-value">${escapeHtml(fmt(report?.kpis?.total_electricity_kwh))}</div><div class="kpi-unit">kWh</div></div>
          <div class="kpi"><div class="kpi-label">平均COP</div><div class="kpi-value">${escapeHtml(fmt(report?.kpis?.average_cop, 3))}</div><div class="kpi-unit">效率指数</div></div>
          <div class="kpi"><div class="kpi-label">异常点数</div><div class="kpi-value">${escapeHtml(String(report?.kpis?.anomaly_count ?? 0))}</div><div class="kpi-unit">个</div></div>
          <div class="kpi"><div class="kpi-label">碳排放估算</div><div class="kpi-value">${escapeHtml(fmt(report?.kpis?.carbon_emission_ton, 3))}</div><div class="kpi-unit">吨CO2</div></div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">图表分析</div>
      <div class="panel-body">
        <div class="grid-2">
          <div class="chart-card"><div class="chart-title">月度能耗统计</div><div id="chart-monthly" class="chart"></div></div>
          <div class="chart-card"><div class="chart-title">分建筑能耗对比</div><div id="chart-comparison" class="chart"></div></div>
          <div class="chart-card"><div class="chart-title">异常分布</div><div id="chart-anomaly" class="chart"></div></div>
          <div class="chart-card"><div class="chart-title">COP效率趋势</div><div id="chart-cop" class="chart"></div></div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">分析结论与建议</div>
      <div class="panel-body">
        <div class="analysis-grid">
          <div>
            <p class="brief">${escapeHtml(report?.analysis?.brief || '')}</p>
            <ul class="list">
              ${(report?.analysis?.conclusions || []).map(item => `<li>${escapeHtml(item)}</li>`).join('')}
            </ul>
          </div>
          <div>
            <ul class="list">
              ${(report?.analysis?.recommendations || []).map(item => `<li>${escapeHtml(item)}</li>`).join('')}
            </ul>
            <div class="row"><span>潜在节能量</span><strong>${escapeHtml(fmt(report?.decision_support?.energy_saving?.potential_savings_kwh))} kWh</strong></div>
            <div class="row"><span>潜在节能率</span><strong>${escapeHtml(fmt(report?.decision_support?.energy_saving?.potential_savings_pct, 2))}%</strong></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"><\/script>
  <script>
    const options = {
      monthly: ${toSafeJSON(monthlyOption)},
      comparison: ${toSafeJSON(comparisonOption)},
      anomaly: ${toSafeJSON(anomalyOption)},
      cop: ${toSafeJSON(copOption)}
    };

    const charts = [
      echarts.init(document.getElementById('chart-monthly')),
      echarts.init(document.getElementById('chart-comparison')),
      echarts.init(document.getElementById('chart-anomaly')),
      echarts.init(document.getElementById('chart-cop'))
    ];

    charts[0].setOption(options.monthly);
    charts[1].setOption(options.comparison);
    charts[2].setOption(options.anomaly);
    charts[3].setOption(options.cop);

    window.addEventListener('resize', () => charts.forEach(c => c.resize()));
  <\/script>
</body>
</html>`

  const blob = new Blob([html], { type: 'text/html;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${reportTitle}.html`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)

  if (!silentSuccess) {
    ElMessage.success('HTML报表导出成功')
  }
}

const triggerAutoActionFromQuery = async () => {
  if (autoActionExecuted.value) return

  const query = route.query || {}
  const autoReport = parseBooleanFlag(query.auto_report)
  const autoExportHtml = String(query.auto_export || '').toLowerCase() === 'html'

  if (!autoReport && !autoExportHtml) {
    return
  }

  autoActionExecuted.value = true

  await generateReport({ silentSuccess: true })

  if (autoExportHtml && reportData.value) {
    exportHtmlReport({ silentSuccess: true })
    ElMessage.success('已按智能助手指令自动生成并导出HTML报表')
    return
  }

  if (reportData.value) {
    ElMessage.success('已按智能助手指令自动生成可视化报表')
  }
}

const resizeCharts = () => {
  Object.values(chartInstances).forEach((chart) => {
    if (chart) chart.resize()
  })
}

onMounted(async () => {
  await loadBuildings()
  applyQueryParamsToForm()
  window.addEventListener('resize', resizeCharts)
  await triggerAutoActionFromQuery()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  Object.keys(chartInstances).forEach((key) => {
    if (chartInstances[key]) {
      chartInstances[key].dispose()
      chartInstances[key] = null
    }
  })
})
</script>

<style scoped>
.agent-report-page {
  padding: 16px;
}

.control-card {
  margin-bottom: 16px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.header-row h2 {
  margin: 0;
  font-size: 22px;
}

.header-row p {
  margin: 8px 0 0;
  color: #6b7280;
}

.unit-tip {
  margin-left: 8px;
  color: #6b7280;
  font-size: 12px;
}

.kpi-grid,
.chart-grid,
.analysis-grid {
  margin-bottom: 16px;
}

.kpi-card {
  border-radius: 10px;
}

.kpi-label {
  color: #6b7280;
  font-size: 13px;
}

.kpi-value {
  margin-top: 8px;
  font-size: 26px;
  font-weight: 700;
  color: #0f172a;
}

.kpi-unit {
  margin-top: 6px;
  font-size: 12px;
  color: #6b7280;
}

.chart-box {
  height: 320px;
}

.brief {
  margin: 0 0 12px;
  color: #475569;
}

.analysis-list {
  margin: 0;
  padding-left: 18px;
  line-height: 1.8;
  color: #1f2937;
}

.decision-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  color: #374151;
}

@media (max-width: 768px) {
  .header-row {
    flex-direction: column;
  }

  .header-actions {
    width: 100%;
  }

  .chart-box {
    height: 260px;
  }
}
</style>
