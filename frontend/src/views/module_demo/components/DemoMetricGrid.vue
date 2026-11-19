<template>
  <div class="demo-summary-grid">
    <el-card v-for="metric in metrics" :key="metric.label" class="demo-card demo-metric-card" shadow="never">
      <span class="demo-metric-label">{{ metric.label }}</span>
      <strong class="demo-metric-value">{{ metric.value }}</strong>
      <span class="demo-metric-note">{{ metric.note }}</span>
    </el-card>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  metrics: Array<{
    label: string
    value: string | number
    note: string
  }>
}>()
</script>
