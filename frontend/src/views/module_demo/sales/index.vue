<template>
  <DemoPageShell title="销售分析" description="用区域、渠道和产品三个维度观察销售额与订单量；点击柱状图可以继续查看下一级明细。">
    <el-card class="demo-filter-card" shadow="never">
      <div class="demo-filter-grid">
        <el-form-item label="统计周期">
          <el-select v-model="period" style="width: 100%">
            <el-option label="近 7 天" value="7d" />
            <el-option label="近 30 天" value="30d" />
            <el-option label="本季度" value="quarter" />
          </el-select>
        </el-form-item>

        <el-form-item label="分析维度">
          <el-select v-model="dimension" style="width: 100%">
            <el-option label="区域" value="region" />
            <el-option label="渠道" value="channel" />
            <el-option label="产品线" value="product" />
          </el-select>
        </el-form-item>

        <el-form-item label="统计指标">
          <el-select v-model="metric" style="width: 100%">
            <el-option label="销售额" value="revenue" />
            <el-option label="订单数" value="orders" />
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
              <strong>{{ dimensionLabel }}分布</strong>
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


        <IndustrialChart :option="distributionOption" height="310px" @chart-click="handleChartClick" />
      </el-card>

      <el-card class="demo-card demo-chart-card" shadow="never">
        <template #header>
          <div class="demo-card-heading">
            <strong>周期趋势</strong>
            <span class="demo-card-code">TREND</span>
          </div>
        </template>

        <p class="demo-chart-note">当前筛选条件下的趋势示例，后续可替换为接口返回的时间序列。</p>
        <IndustrialChart :option="trendOption" height="310px" />
      </el-card>

      <el-card class="demo-card demo-table-card demo-chart-card--wide" shadow="never">
        <template #header>
          <div class="demo-card-heading">
            <div>
              <strong>明细表</strong>
              <span class="demo-card-note"> · 当前层级：{{ currentLevelLabel }}</span>
            </div>
            <el-tag size="small" effect="plain">{{ tableRows.length }} 条示例记录</el-tag>
          </div>
        </template>

        <el-table :data="tableRows" border stripe class="demo-table" row-key="code">
          <el-table-column prop="name" label="分析项" min-width="180" />
          <el-table-column prop="code" label="编码" width="150">
            <template #default="{ row }"><code>{{ row.code }}</code></template>
          </el-table-column>
          <el-table-column prop="value" :label="metricLabel" width="150" align="right">
            <template #default="{ row }"><span class="number-cell">{{ row.value }}</span></template>
          </el-table-column>
          <el-table-column prop="orders" label="订单数" width="130" align="right">
            <template #default="{ row }"><span class="number-cell">{{ row.orders }}</span></template>
          </el-table-column>
          <el-table-column prop="share" label="占当前层级" width="140" align="right">
            <template #default="{ row }"><span class="number-cell">{{ row.share }}%</span></template>
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

defineOptions({ name: 'DemoSalesAnalysis' })

type SalesDimension = 'region' | 'channel' | 'product'
type SalesMetric = 'revenue' | 'orders'
type Period = '7d' | '30d' | 'quarter'

interface SalesNode {
  name: string
  code: string
  revenue: number
  orders: number
  children?: SalesNode[]
}

const salesTrees: Record<SalesDimension, SalesNode[]> = {
  region: [
    {
      name: '华东', code: 'REG-EAST', revenue: 428, orders: 1260,
      children: [
        {
          name: '上海', code: 'CITY-SH', revenue: 236, orders: 710, children: [
            { name: '旗舰店', code: 'STORE-SH-01', revenue: 142, orders: 430 },
            { name: '企业客户', code: 'B2B-SH-01', revenue: 94, orders: 280 },
          ]
        },
        {
          name: '杭州', code: 'CITY-HZ', revenue: 192, orders: 550, children: [
            { name: '直营网点', code: 'STORE-HZ-01', revenue: 108, orders: 320 },
            { name: '合作渠道', code: 'CHANNEL-HZ-01', revenue: 84, orders: 230 },
          ]
        },
      ],
    },
    {
      name: '华南', code: 'REG-SOUTH', revenue: 356, orders: 980,
      children: [
        {
          name: '深圳', code: 'CITY-SZ', revenue: 208, orders: 590, children: [
            { name: '直营网点', code: 'STORE-SZ-01', revenue: 128, orders: 360 },
            { name: '企业客户', code: 'B2B-SZ-01', revenue: 80, orders: 230 },
          ]
        },
        {
          name: '广州', code: 'CITY-GZ', revenue: 148, orders: 390, children: [
            { name: '旗舰店', code: 'STORE-GZ-01', revenue: 92, orders: 250 },
            { name: '合作渠道', code: 'CHANNEL-GZ-01', revenue: 56, orders: 140 },
          ]
        },
      ],
    },
    {
      name: '华北', code: 'REG-NORTH', revenue: 286, orders: 760,
      children: [
        {
          name: '北京', code: 'CITY-BJ', revenue: 174, orders: 480, children: [
            { name: '旗舰店', code: 'STORE-BJ-01', revenue: 102, orders: 290 },
            { name: '企业客户', code: 'B2B-BJ-01', revenue: 72, orders: 190 },
          ]
        },
        {
          name: '天津', code: 'CITY-TJ', revenue: 112, orders: 280, children: [
            { name: '直营网点', code: 'STORE-TJ-01', revenue: 64, orders: 160 },
            { name: '合作渠道', code: 'CHANNEL-TJ-01', revenue: 48, orders: 120 },
          ]
        },
      ],
    },
  ],
  channel: [
    {
      name: '直营', code: 'CH-DIRECT', revenue: 402, orders: 1180,
      children: [
        { name: '直营网点', code: 'DIRECT-STORE', revenue: 236, orders: 690 },
        { name: '企业客户', code: 'DIRECT-B2B', revenue: 166, orders: 490 },
      ],
    },
    {
      name: '经销', code: 'CH-DEALER', revenue: 318, orders: 860,
      children: [
        { name: '区域经销', code: 'DEALER-REGION', revenue: 188, orders: 510 },
        { name: '行业合作', code: 'DEALER-INDUSTRY', revenue: 130, orders: 350 },
      ],
    },
    {
      name: '线上', code: 'CH-ONLINE', revenue: 350, orders: 960,
      children: [
        { name: '商城', code: 'ONLINE-MALL', revenue: 210, orders: 570 },
        { name: '平台店铺', code: 'ONLINE-MARKET', revenue: 140, orders: 390 },
      ],
    },
  ],
  product: [
    {
      name: '智能终端', code: 'PROD-DEVICE', revenue: 386, orders: 840,
      children: [
        { name: '标准版', code: 'DEVICE-STANDARD', revenue: 220, orders: 510 },
        { name: '专业版', code: 'DEVICE-PRO', revenue: 166, orders: 330 },
      ],
    },
    {
      name: '管理软件', code: 'PROD-SOFTWARE', revenue: 428, orders: 1240,
      children: [
        { name: '基础模块', code: 'SOFTWARE-BASE', revenue: 246, orders: 730 },
        { name: '高级模块', code: 'SOFTWARE-PRO', revenue: 182, orders: 510 },
      ],
    },
    {
      name: '服务方案', code: 'PROD-SERVICE', revenue: 256, orders: 820,
      children: [
        { name: '实施服务', code: 'SERVICE-IMPLEMENT', revenue: 144, orders: 420 },
        { name: '运维服务', code: 'SERVICE-OPS', revenue: 112, orders: 400 },
      ],
    },
  ],
}

const period = ref<Period>('30d')
const dimension = ref<SalesDimension>('region')
const metric = ref<SalesMetric>('revenue')
const drillPath = ref<string[]>([])

const periodScale: Record<Period, number> = {
  '7d': .28,
  '30d': 1,
  quarter: 2.55,
}

const periodLabels: Record<Period, string> = {
  '7d': '近 7 天',
  '30d': '近 30 天',
  quarter: '本季度',
}

const dimensionLabels: Record<SalesDimension, string> = {
  region: '区域',
  channel: '渠道',
  product: '产品线',
}

const metricLabel = computed(() => metric.value === 'revenue' ? '销售额（万元）' : '订单数')
const dimensionLabel = computed(() => dimensionLabels[dimension.value])

const activeNodes = computed(() => {
  let nodes = salesTrees[dimension.value]

  for (const parentName of drillPath.value) {
    const parent = nodes.find(node => node.name === parentName)
    nodes = parent?.children || []
  }

  return nodes
})

const currentLevelLabel = computed(() => {
  return drillPath.value[drillPath.value.length - 1] || dimensionLabel.value
})

const valueOf = (node: SalesNode) => {
  if (metric.value === 'orders') {
    return Math.round(node.orders * periodScale[period.value])
  }

  return Math.round(node.revenue * periodScale[period.value])
}

const tableRows = computed(() => {
  const total = activeNodes.value.reduce((sum, node) => sum + valueOf(node), 0) || 1

  return activeNodes.value.map(node => ({
    name: node.name,
    code: node.code,
    value: valueOf(node),
    orders: Math.round(node.orders * periodScale[period.value]),
    share: Number(((valueOf(node) / total) * 100).toFixed(1)),
    hasChildren: Boolean(node.children?.length),
  }))
})

const summaryMetrics = computed(() => [
  {
    label: metricLabel.value,
    value: metric.value === 'revenue'
      ? `${tableRows.value.reduce((sum, row) => sum + row.value, 0)} 万元`
      : `${tableRows.value.reduce((sum, row) => sum + row.value, 0)} 单`,
    note: periodLabels[period.value],
  },
  {
    label: '当前层级',
    value: currentLevelLabel.value,
    note: '点击图表可继续下钻',
  },
  {
    label: '分析项数',
    value: tableRows.value.length,
    note: `按${dimensionLabel.value}统计`,
  },
  {
    label: '数据状态',
    value: 'Demo',
    note: '后续替换为真实接口',
  },
])

const distributionOption = computed<EChartsOption>(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
    valueFormatter: value => metric.value === 'revenue' ? `${value} 万元` : `${value} 单`,
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
    axisLabel: { color: '#68736c' },
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

const trendLabels = computed(() => {
  if (period.value === '7d') return ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  if (period.value === 'quarter') return ['第 1 月', '第 2 月', '第 3 月']
  return ['第 1 周', '第 2 周', '第 3 周', '第 4 周']
})

const trendOption = computed<EChartsOption>(() => {
  const total = tableRows.value.reduce((sum, row) => sum + row.value, 0)
  const ratios = [0.72, 0.86, 0.79, 1.08, 1.14, 1.02, 1.2]
  const data = trendLabels.value.map((_, index) => Math.round(total * (ratios[index % ratios.length] || 1) / trendLabels.value.length))

  return {
    tooltip: {
      trigger: 'axis',
      valueFormatter: value => metric.value === 'revenue' ? `${value} 万元` : `${value} 单`,
    },
    grid: { left: 48, right: 18, top: 20, bottom: 42 },
    xAxis: {
      type: 'category',
      data: trendLabels.value,
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
      areaStyle: { color: 'rgba(35, 173, 229, .10)' },
      data,
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
