<template>
  <div class="industrial-chart" :style="{ height }">
    <el-empty v-if="isEmpty" description="暂无图表数据" :image-size="56" />
    <div v-else ref="chartRef" class="industrial-chart__canvas" />
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

const props = withDefaults(defineProps<{
  option: EChartsOption
  height?: string
  loading?: boolean
  isEmpty?: boolean
}>(), {
  height: '260px',
  loading: false,
  isEmpty: false,
})

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | undefined
let resizeObserver: ResizeObserver | undefined

function renderChart() {
  if (!chartRef.value || props.isEmpty) return
  chart ??= echarts.init(chartRef.value, undefined, { renderer: 'canvas' })
  chart.setOption(props.option, { notMerge: true })
  chart.resize()
}

onMounted(async () => {
  await nextTick()
  renderChart()
  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => chart?.resize())
    resizeObserver.observe(chartRef.value)
  }
})

watch(() => [props.option, props.isEmpty], () => nextTick(renderChart), { deep: true })

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  chart?.dispose()
  chart = undefined
})
</script>

<style scoped lang="scss">
.industrial-chart,
.industrial-chart__canvas {
  width: 100%;
}

.industrial-chart :deep(.el-empty) {
  height: 100%;
  padding: 0;
}
</style>
