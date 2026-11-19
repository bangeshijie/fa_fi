<template>
  <DemoPageShell title="现金流分析" description="按现金流分类、账户和责任部门查看资金流入与流出，柱状图支持从汇总层级进入明细。">
    <el-card class="demo-filter-card" shadow="never">
      <div class="demo-filter-grid">
        <el-form-item label="统计周期">
          <el-select v-model="period" style="width: 100%">
            <el-option label="本月" value="month" />
            <el-option label="本季度" value="quarter" />
            <el-option label="本年度" value="year" />
          </el-select>
        </el-form-item>

        <el-form-item label="分析维度">
          <el-select v-model="dimension" style="width: 100%">
            <el-option label="现金流分类" value="category" />
            <el-option label="资金账户" value="account" />
            <el-option label="责任部门" value="department" />
          </el-select>
        </el-form-item>

        <el-form-item label="统计指标">
          <el-select v-model="metric" style="width: 100%">
            <el-option label="净现金流" value="net" />
            <el-option label="流入金额" value="inflow" />
            <el-option label="流出金额" value="outflow" />
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
              <strong>{{ dimensionLabel }}现金流</strong>
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

        <IndustrialChart :option="cashflowOption" height="310px" @chart-click="handleChartClick" />
      </el-card>

      <el-card class="demo-card demo-chart-card" shadow="never">
        <template #header>
          <div class="demo-card-heading">
            <strong>净现金流趋势</strong>
            <span class="demo-card-code">TREND</span>
          </div>
        </template>

        <p class="demo-chart-note">正值表示流入大于流出，负值表示当期净流出。</p>
        <IndustrialChart :option="trendOption" height="310px" />
      </el-card>

      <el-card class="demo-card demo-table-card demo-chart-card--wide" shadow="never">
        <template #header>
          <div class="demo-card-heading">
            <div>
              <strong>资金明细表</strong>
              <span class="demo-card-note"> · 当前层级：{{ currentLevelLabel }}</span>
            </div>
            <el-tag size="small" effect="plain">{{ tableRows.length }} 条示例记录</el-tag>
          </div>
        </template>

        <el-table :data="tableRows" border stripe class="demo-table" row-key="code">
          <el-table-column prop="name" label="分析项" min-width="180" />
          <el-table-column prop="code" label="编码" width="170">
            <template #default="{ row }"><code>{{ row.code }}</code></template>
          </el-table-column>
          <el-table-column prop="inflow" label="流入（万元）" width="150" align="right">
            <template #default="{ row }"><span class="number-cell">{{ row.inflow }}</span></template>
          </el-table-column>
          <el-table-column prop="outflow" label="流出（万元）" width="150" align="right">
            <template #default="{ row }"><span class="number-cell">{{ row.outflow }}</span></template>
          </el-table-column>
          <el-table-column prop="net" label="净额（万元）" width="150" align="right">
            <template #default="{ row }"><span class="number-cell">{{ row.net }}</span></template>
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

defineOptions({ name: 'DemoCashflowAnalysis' })

type CashDimension = 'category' | 'account' | 'department'
type CashMetric = 'net' | 'inflow' | 'outflow'
type CashPeriod = 'month' | 'quarter' | 'year'

interface CashNode {
  name: string
  code: string
  inflow: number
  outflow: number
  children?: CashNode[]
}

const cashflowTrees: Record<CashDimension, CashNode[]> = {
  category: [
    {
      name: '经营活动', code: 'CF-OPERATING', inflow: 620, outflow: 430, children: [
        { name: '销售回款', code: 'CF-OPERATING-SALES', inflow: 420, outflow: 80 },
        { name: '供应商结算', code: 'CF-OPERATING-SUPPLIER', inflow: 90, outflow: 220 },
        { name: '人员与行政', code: 'CF-OPERATING-STAFF', inflow: 110, outflow: 130 },
      ]
    },
    {
      name: '投资活动', code: 'CF-INVESTING', inflow: 160, outflow: 310, children: [
        { name: '资产处置', code: 'CF-INVESTING-SELL', inflow: 80, outflow: 20 },
        { name: '设备采购', code: 'CF-INVESTING-ASSET', inflow: 40, outflow: 190 },
        { name: '长期投资', code: 'CF-INVESTING-LONG', inflow: 40, outflow: 100 },
      ]
    },
    {
      name: '筹资活动', code: 'CF-FINANCING', inflow: 270, outflow: 150, children: [
        { name: '融资到账', code: 'CF-FINANCING-IN', inflow: 220, outflow: 20 },
        { name: '利息与分配', code: 'CF-FINANCING-DIV', inflow: 50, outflow: 130 },
      ]
    },
  ],
  account: [
    {
      name: '经营账户', code: 'ACC-OPERATING', inflow: 560, outflow: 380, children: [
        { name: '客户回款', code: 'ACC-OPERATING-IN', inflow: 410, outflow: 40 },
        { name: '日常支出', code: 'ACC-OPERATING-OUT', inflow: 150, outflow: 340 },
      ]
    },
    {
      name: '结算账户', code: 'ACC-SETTLEMENT', inflow: 310, outflow: 260, children: [
        { name: '平台结算', code: 'ACC-SETTLEMENT-PLATFORM', inflow: 200, outflow: 100 },
        { name: '供应链结算', code: 'ACC-SETTLEMENT-SUPPLY', inflow: 110, outflow: 160 },
      ]
    },
    {
      name: '专项账户', code: 'ACC-SPECIAL', inflow: 180, outflow: 250, children: [
        { name: '项目资金', code: 'ACC-SPECIAL-PROJECT', inflow: 100, outflow: 170 },
        { name: '保证金', code: 'ACC-SPECIAL-DEPOSIT', inflow: 80, outflow: 80 },
      ]
    },
  ],
  department: [
    {
      name: '销售中心', code: 'DEPT-SALES', inflow: 520, outflow: 250, children: [
        { name: '客户回款', code: 'DEPT-SALES-IN', inflow: 420, outflow: 90 },
        { name: '市场活动', code: 'DEPT-SALES-MKT', inflow: 100, outflow: 160 },
      ]
    },
    {
      name: '研发院', code: 'DEPT-DELIVERY', inflow: 330, outflow: 410, children: [
        { name: '项目收款', code: 'DEPT-DELIVERY-IN', inflow: 200, outflow: 100 },
        { name: '实施采购', code: 'DEPT-DELIVERY-OUT', inflow: 130, outflow: 310 },
      ]
    },
    {
      name: '管理中心', code: 'DEPT-ADMIN', inflow: 200, outflow: 230, children: [
        { name: '内部划拨', code: 'DEPT-ADMIN-IN', inflow: 80, outflow: 70 },
        { name: '固定支出', code: 'DEPT-ADMIN-OUT', inflow: 120, outflow: 160 },
      ]
    },
  ],
}

const period = ref<CashPeriod>('quarter')
const dimension = ref<CashDimension>('category')
const metric = ref<CashMetric>('net')
const drillPath = ref<string[]>([])

const periodScale: Record<CashPeriod, number> = {
  month: .35,
  quarter: 1,
  year: 3.7,
}

const periodLabels: Record<CashPeriod, string> = {
  month: '本月',
  quarter: '本季度',
  year: '本年度',
}

const dimensionLabels: Record<CashDimension, string> = {
  category: '现金流分类',
  account: '资金账户',
  department: '责任部门',
}

const metricLabels: Record<CashMetric, string> = {
  net: '净现金流',
  inflow: '流入金额',
  outflow: '流出金额',
}

const dimensionLabel = computed(() => dimensionLabels[dimension.value])
const metricLabel = computed(() => metricLabels[metric.value])

const activeNodes = computed(() => {
  let nodes = cashflowTrees[dimension.value]

  for (const parentName of drillPath.value) {
    const parent = nodes.find(node => node.name === parentName)
    nodes = parent?.children || []
  }

  return nodes
})

const currentLevelLabel = computed(() => drillPath.value[drillPath.value.length - 1] || dimensionLabel.value)

const scaleNodeValue = (value: number) => Math.round(value * periodScale[period.value])

const tableRows = computed(() => activeNodes.value.map(node => {
  const inflow = scaleNodeValue(node.inflow)
  const outflow = scaleNodeValue(node.outflow)

  return {
    name: node.name,
    code: node.code,
    inflow,
    outflow,
    net: inflow - outflow,
    hasChildren: Boolean(node.children?.length),
  }
}))

const metricValue = computed(() => {
  if (metric.value === 'inflow') return tableRows.value.reduce((sum, row) => sum + row.inflow, 0)
  if (metric.value === 'outflow') return tableRows.value.reduce((sum, row) => sum + row.outflow, 0)
  return tableRows.value.reduce((sum, row) => sum + row.net, 0)
})

const summaryMetrics = computed(() => [
  {
    label: metricLabel.value,
    value: `${metricValue.value} 万元`,
    note: periodLabels[period.value],
  },
  {
    label: '当前层级',
    value: currentLevelLabel.value,
    note: '点击图表可继续下钻',
  },
  {
    label: '流入合计',
    value: `${tableRows.value.reduce((sum, row) => sum + row.inflow, 0)} 万元`,
    note: '当前筛选结果',
  },
  {
    label: '数据状态',
    value: 'Demo',
    note: '后续替换为真实接口',
  },
])

const cashflowOption = computed<EChartsOption>(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
    valueFormatter: value => `${value} 万元`,
  },
  legend: {
    top: 0,
    textStyle: { color: '#68736c' },
  },
  grid: { left: 48, right: 18, top: 42, bottom: 42 },
  xAxis: {
    type: 'category',
    data: tableRows.value.map(row => row.name),
    axisLabel: { color: '#68736c', interval: 0, rotate: tableRows.value.length > 5 ? 25 : 0 },
    axisLine: { lineStyle: { color: '#d8e0d9' } },
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: '#68736c' },
    splitLine: { lineStyle: { color: '#e8ede8' } },
  },
  series: [
    {
      type: 'bar',
      name: '流入',
      barMaxWidth: 28,
      itemStyle: { color: '#23ADE5' },
      data: tableRows.value.map(row => row.inflow),
    },
    {
      type: 'bar',
      name: '流出',
      barMaxWidth: 28,
      itemStyle: { color: '#FFB800' },
      data: tableRows.value.map(row => -row.outflow),
    },
  ],
}))

const trendOption = computed<EChartsOption>(() => {
  const labels = period.value === 'year'
    ? ['一季度', '二季度', '三季度', '四季度']
    : period.value === 'month'
      ? ['第 1 周', '第 2 周', '第 3 周', '第 4 周']
      : ['第 1 月', '第 2 月', '第 3 月']
  const base = metricValue.value / labels.length
  const ratios = [0.84, 1.08, .92, 1.16]

  return {
    tooltip: {
      trigger: 'axis',
      valueFormatter: value => `${value} 万元`,
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
      axisLabel: { color: '#68736c' },
      splitLine: { lineStyle: { color: '#e8ede8' } },
    },
    series: [{
      type: 'line',
      name: metricLabel.value,
      smooth: true,
      symbolSize: 7,
      itemStyle: { color: '#23ADE5' },
      lineStyle: { color: '#23ADE5', width: 2 },
      data: labels.map((_, index) => Math.round(base * (ratios[index] || 1))),
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
