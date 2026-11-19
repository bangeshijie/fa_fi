<template>
  <div class="industrial-chart" :style="{ height }" :aria-busy="loading">
    <el-empty v-if="isEmpty" description="暂无图表数据" :image-size="56" />
    <div v-else ref="chartRef" class="industrial-chart__canvas" />

    <div v-if="loading" class="industrial-chart__loading" role="status">
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
      <span>图表加载中</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

interface ChartClickPayload {
  name?: string
  dataIndex?: number
  seriesName?: string
  data?: unknown
  value?: unknown
}

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


const emit = defineEmits<{
  (event: 'chart-click', payload: ChartClickPayload): void
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | undefined
let resizeObserver: ResizeObserver | undefined

function renderChart() {
  if (!chartRef.value || props.isEmpty) return
  chart ??= echarts.init(chartRef.value, undefined, { renderer: 'canvas' })

  chart.off('click')
  chart.on('click', (params) => {
    emit('chart-click', params as ChartClickPayload)
  })

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

watch(
  () => [props.option, props.isEmpty, props.loading],
  () => nextTick(renderChart),
  { deep: true },
)

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

.industrial-chart {
  position: relative;
  min-height: 160px;
}

.industrial-chart__canvas {
  height: 100%;
}

.industrial-chart__loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: var(--app-overlay-bg);
  color: var(--el-color-primary);
  font-size: 12px;
}

.industrial-chart :deep(.el-empty) {
  height: 100%;
  padding: 0;
}
</style>
