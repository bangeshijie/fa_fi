<template>
  <DemoPageShell title="经营效率分析" description="比较部门、流程和渠道的完成率、处理效率与成本，用图表点击快速定位到下一级执行单元。">
    <el-card class="demo-filter-card" shadow="never">
      <div class="demo-filter-grid">
        <el-form-item label="统计周期">
          <el-select v-model="period" style="width: 100%">
            <el-option label="本周" value="week" />
            <el-option label="本月" value="month" />
            <el-option label="本季度" value="quarter" />
          </el-select>
        </el-form-item>

        <el-form-item label="分析维度">
          <el-select v-model="dimension" style="width: 100%">
            <el-option label="部门" value="department" />
            <el-option label="业务流程" value="process" />
            <el-option label="服务渠道" value="channel" />
          </el-select>
        </el-form-item>

        <el-form-item label="统计指标">
          <el-select v-model="metric" style="width: 100%">
            <el-option label="完成率" value="completion" />
            <el-option label="处理效率" value="efficiency" />
            <el-option label="单位成本" value="cost" />
          </el-select>
        </el-form-item>

        <el-form-item label="数据来源">
          <el-tag type="info" effect="plain">前端示例数据</el-tag>
        </el-form-item>
      </div>
    </el-card>

    <DemoMetricGrid :metrics="summaryMetrics" />

    <div class="demo-content-grid">
      <el-card class="demo-card demo-chart-card" shadow="never">
        <template #header>
          <div class="demo-card-heading">
            <div>
              <strong>{{ dimensionLabel }}表现</strong>
              <span class="demo-card-note"> · 点击柱体进入下一级</span>
            </div>
            <span class="demo-card-code">DRILL / {{ drillPath.length + 1 }}</span>
          </div>
        </template>

        <div class="demo-drilldown" aria-label="当前下钻路径">
          <template v-for="(item, index) in drillBreadcrumb" :key="`${item}-${index}`">
            <button class="demo-drilldown__button" type="button" @click="jumpTo(index)">
              {{ item }}
            </button>
            <span v-if="index < drillBreadcrumb.length - 1" class="demo-drilldown__separator">/</span>
          </template>
        </div>

        <IndustrialChart :option="performanceOption" height="310px" @chart-click="handleChartClick" />
      </el-card>

      <el-card class="demo-card demo-chart-card" shadow="never">
        <template #header>
          <div class="demo-card-heading">
            <strong>周期趋势</strong>
            <span class="demo-card-code">TREND</span>
          </div>
        </template>

        <p class="demo-chart-note">筛选指标改变后，趋势图和右侧明细会同步刷新。</p>
        <IndustrialChart :option="trendOption" height="310px" />
      </el-card>

      <el-card class="demo-card demo-table-card demo-chart-card--wide" shadow="never">
        <template #header>
          <div class="demo-card-heading">
            <div>
              <strong>执行明细表</strong>
              <span class="demo-card-note"> · 当前层级：{{ currentLevelLabel }}</span>
            </div>
            <el-tag size="small" effect="plain">{{ tableRows.length }} 条示例记录</el-tag>
          </div>
        </template>

        <el-table :data="tableRows" border stripe class="demo-table" row-key="code">
          <el-table-column prop="name" label="分析项" min-width="180" />
          <el-table-column prop="code" label="编码" width="180">
            <template #default="{ row }"><code>{{ row.code }}</code></template>
          </el-table-column>
          <el-table-column prop="value" :label="metricLabel" width="150" align="right">
            <template #default="{ row }"><span class="number-cell">{{ formatMetric(row.value) }}</span></template>
          </el-table-column>
          <el-table-column prop="volume" label="处理量" width="130" align="right">
            <template #default="{ row }"><span class="number-cell">{{ row.volume }}</span></template>
          </el-table-column>
          <el-table-column prop="change" label="环比" width="120" align="right">
            <template #default="{ row }"><span class="number-cell">{{ row.change > 0 ? '+' : '' }}{{ row.change
                }}%</span></template>
          </el-table-column>
          <el-table-column label="下钻" width="110" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.hasChildren" link type="primary" @click="drillInto(row.name)">
                查看下级
              </el-button>
              <span v-else class="demo-card-note">末级</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </DemoPageShell>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { EChartsOption } from 'echarts'

import IndustrialChart from '@/components/charts/IndustrialChart.vue'
import DemoMetricGrid from '../components/DemoMetricGrid.vue'
import DemoPageShell from '../components/DemoPageShell.vue'

defineOptions({ name: 'DemoOperationsAnalysis' })

type OpsDimension = 'department' | 'process' | 'channel'
type OpsMetric = 'completion' | 'efficiency' | 'cost'
type OpsPeriod = 'week' | 'month' | 'quarter'

interface OpsNode {
  name: string
  code: string
  completion: number
  efficiency: number
  cost: number
  volume: number
  change: number
  children?: OpsNode[]
}

const operationsTrees: Record<OpsDimension, OpsNode[]> = {
  department: [
    {
      name: '销售中心', code: 'OPS-SALES', completion: 94, efficiency: 88, cost: 18, volume: 1260, change: 6, children: [
        { name: '客户响应', code: 'OPS-SALES-RESPONSE', completion: 96, efficiency: 91, cost: 11, volume: 720, change: 8 },
        { name: '商机转化', code: 'OPS-SALES-CONVERT', completion: 91, efficiency: 84, cost: 25, volume: 540, change: 4 },
      ]
    },
    {
      name: '研发院', code: 'OPS-DELIVERY', completion: 89, efficiency: 82, cost: 26, volume: 880, change: -2, children: [
        { name: '项目实施', code: 'OPS-DELIVERY-IMPLEMENT', completion: 87, efficiency: 78, cost: 31, volume: 420, change: -4 },
        { name: '服务验收', code: 'OPS-DELIVERY-ACCEPT', completion: 92, efficiency: 86, cost: 21, volume: 460, change: 1 },
      ]
    },
    {
      name: '管理中心', code: 'OPS-ADMIN', completion: 96, efficiency: 93, cost: 12, volume: 630, change: 5, children: [
        { name: '财务处理', code: 'OPS-ADMIN-FINANCE', completion: 97, efficiency: 94, cost: 10, volume: 360, change: 7 },
        { name: '人事服务', code: 'OPS-ADMIN-HR', completion: 95, efficiency: 91, cost: 14, volume: 270, change: 3 },
      ]
    },
  ],
  process: [
    {
      name: '订单处理', code: 'OPS-PROCESS-ORDER', completion: 95, efficiency: 90, cost: 16, volume: 1420, change: 4, children: [
        { name: '订单审核', code: 'OPS-PROCESS-ORDER-AUDIT', completion: 97, efficiency: 92, cost: 12, volume: 760, change: 6 },
        { name: '订单履约', code: 'OPS-PROCESS-ORDER-FULFILL', completion: 93, efficiency: 88, cost: 20, volume: 660, change: 2 },
      ]
    },
    {
      name: '合同管理', code: 'OPS-PROCESS-CONTRACT', completion: 90, efficiency: 84, cost: 22, volume: 620, change: -1, children: [
        { name: '合同评审', code: 'OPS-PROCESS-CONTRACT-REVIEW', completion: 92, efficiency: 86, cost: 20, volume: 340, change: 1 },
        { name: '合同归档', code: 'OPS-PROCESS-CONTRACT-ARCHIVE', completion: 88, efficiency: 81, cost: 24, volume: 280, change: -3 },
      ]
    },
    {
      name: '售后服务', code: 'OPS-PROCESS-SERVICE', completion: 86, efficiency: 79, cost: 29, volume: 510, change: 2, children: [
        { name: '问题受理', code: 'OPS-PROCESS-SERVICE-IN', completion: 89, efficiency: 83, cost: 25, volume: 310, change: 4 },
        { name: '问题解决', code: 'OPS-PROCESS-SERVICE-OUT', completion: 82, efficiency: 74, cost: 35, volume: 200, change: -1 },
      ]
    },
  ],
  channel: [
    {
      name: '直营网点', code: 'OPS-CHANNEL-DIRECT', completion: 93, efficiency: 87, cost: 19, volume: 980, change: 5, children: [
        { name: '门店服务', code: 'OPS-CHANNEL-DIRECT-STORE', completion: 95, efficiency: 90, cost: 16, volume: 590, change: 7 },
        { name: '企业服务', code: 'OPS-CHANNEL-DIRECT-B2B', completion: 90, efficiency: 83, cost: 24, volume: 390, change: 2 },
      ]
    },
    {
      name: '合作渠道', code: 'OPS-CHANNEL-PARTNER', completion: 88, efficiency: 80, cost: 27, volume: 720, change: -2, children: [
        { name: '区域合作', code: 'OPS-CHANNEL-PARTNER-REGION', completion: 90, efficiency: 83, cost: 24, volume: 420, change: 1 },
        { name: '行业合作', code: 'OPS-CHANNEL-PARTNER-INDUSTRY', completion: 85, efficiency: 76, cost: 31, volume: 300, change: -5 },
      ]
    },
    {
      name: '线上平台', code: 'OPS-CHANNEL-ONLINE', completion: 97, efficiency: 94, cost: 10, volume: 1320, change: 9, children: [
        { name: '商城订单', code: 'OPS-CHANNEL-ONLINE-MALL', completion: 98, efficiency: 95, cost: 9, volume: 850, change: 10 },
        { name: '平台订单', code: 'OPS-CHANNEL-ONLINE-MARKET', completion: 96, efficiency: 92, cost: 12, volume: 470, change: 7 },
      ]
    },
  ],
}

const period = ref<OpsPeriod>('month')
const dimension = ref<OpsDimension>('department')
const metric = ref<OpsMetric>('completion')
const drillPath = ref<string[]>([])

const periodScale: Record<OpsPeriod, number> = {
  week: .25,
  month: 1,
  quarter: 2.8,
}

const periodLabels: Record<OpsPeriod, string> = {
  week: '本周',
  month: '本月',
  quarter: '本季度',
}

const dimensionLabels: Record<OpsDimension, string> = {
  department: '部门',
  process: '业务流程',
  channel: '服务渠道',
}

const metricLabels: Record<OpsMetric, string> = {
  completion: '完成率（%）',
  efficiency: '处理效率（%）',
  cost: '单位成本（万元）',
}

const dimensionLabel = computed(() => dimensionLabels[dimension.value])
const metricLabel = computed(() => metricLabels[metric.value])

const activeNodes = computed(() => {
  let nodes = operationsTrees[dimension.value]

  for (const parentName of drillPath.value) {
    const parent = nodes.find(node => node.name === parentName)
    nodes = parent?.children || []
  }

  return nodes
})

const currentLevelLabel = computed(() => drillPath.value[drillPath.value.length - 1] || dimensionLabel.value)

const valueOf = (node: OpsNode) => {
  const base = node[metric.value]
  if (metric.value === 'cost') return Number((base * Math.sqrt(periodScale[period.value])).toFixed(1))
  return Number(Math.min(100, base * (period.value === 'week' ? .98 : period.value === 'quarter' ? 1.01 : 1)).toFixed(1))
}

const formatMetric = (value: number) => {
  if (metric.value === 'cost') return `${value} 万元`
  return `${value}%`
}

const tableRows = computed(() => activeNodes.value.map(node => ({
  name: node.name,
  code: node.code,
  value: valueOf(node),
  volume: Math.round(node.volume * periodScale[period.value]),
  change: node.change,
  hasChildren: Boolean(node.children?.length),
})))

const summaryMetrics = computed(() => {
  const average = tableRows.value.length
    ? tableRows.value.reduce((sum, row) => sum + row.value, 0) / tableRows.value.length
    : 0

  return [
    {
      label: '当前均值',
      value: formatMetric(Number(average.toFixed(1))),
      note: periodLabels[period.value],
    },
    {
      label: '当前层级',
      value: currentLevelLabel.value,
      note: '点击图表可继续下钻',
    },
    {
      label: '处理量',
      value: tableRows.value.reduce((sum, row) => sum + row.volume, 0),
      note: '当前筛选结果',
    },
    {
      label: '数据状态',
      value: 'Demo',
      note: '后续替换为真实接口',
    },
  ]
})

const performanceOption = computed<EChartsOption>(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
    valueFormatter: value => metric.value === 'cost' ? `${value} 万元` : `${value}%`,
  },
  grid: { left: 48, right: 18, top: 20, bottom: 42 },
  xAxis: {
    type: 'category',
    data: tableRows.value.map(row => row.name),
    axisLabel: { color: '#68736c', interval: 0, rotate: tableRows.value.length > 5 ? 25 : 0 },
    axisLine: { lineStyle: { color: '#d8e0d9' } },
  },
  yAxis: {
    type: 'value',
    max: metric.value === 'cost' ? undefined : 100,
    axisLabel: { color: '#68736c', formatter: metric.value === 'cost' ? '{value}' : '{value}%' },
    splitLine: { lineStyle: { color: '#e8ede8' } },
  },
  series: [{
    type: 'bar',
    name: metricLabel.value,
    barMaxWidth: 34,
    itemStyle: { color: '#23ADE5' },
    data: tableRows.value.map(row => row.value),
  }],
}))

const trendOption = computed<EChartsOption>(() => {
  const labels = period.value === 'quarter'
    ? ['第 1 月', '第 2 月', '第 3 月']
    : period.value === 'month'
      ? ['第 1 周', '第 2 周', '第 3 周', '第 4 周']
      : ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  const average = tableRows.value.length
    ? tableRows.value.reduce((sum, row) => sum + row.value, 0) / tableRows.value.length
    : 0
  const ratios = [.94, 1.02, .98, 1.08, 1.04, 1.12, 1.06]

  return {
    tooltip: {
      trigger: 'axis',
      valueFormatter: value => metric.value === 'cost' ? `${value} 万元` : `${value}%`,
    },
    grid: { left: 48, right: 18, top: 20, bottom: 42 },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { color: '#68736c' },
      axisLine: { lineStyle: { color: '#d8e0d9' } },
    },
    yAxis: {
      type: 'value',
      max: metric.value === 'cost' ? undefined : 100,
      axisLabel: { color: '#68736c', formatter: metric.value === 'cost' ? '{value}' : '{value}%' },
      splitLine: { lineStyle: { color: '#e8ede8' } },
    },
    series: [{
      type: 'line',
      name: metricLabel.value,
      smooth: true,
      symbolSize: 7,
      itemStyle: { color: '#23ADE5' },
      lineStyle: { color: '#23ADE5', width: 2 },
      data: labels.map((_, index) => {
        const value = average * (ratios[index % ratios.length] || 1)
        return Number(value.toFixed(1))
      }),
    }],
  }
})

const drillBreadcrumb = computed(() => [dimensionLabel.value, ...drillPath.value])

function drillInto(name: string) {
  const node = activeNodes.value.find(item => item.name === name)
  if (node?.children?.length) drillPath.value.push(name)
}

function handleChartClick(payload: unknown) {
  if (!payload || typeof payload !== 'object') return
  const dataIndex = Number((payload as { dataIndex?: unknown }).dataIndex)
  const node = activeNodes.value[dataIndex]
  if (node?.children?.length) drillPath.value.push(node.name)
}

function jumpTo(index: number) {
  drillPath.value = drillPath.value.slice(0, index)
}

watch([dimension, period, metric], () => {
  drillPath.value = []
})
</script>
