<template>
  <section class="demo-page-shell">
    <header class="demo-page-heading">
      <div>
        <div class="demo-page-kicker">模块示例 / 演示数据</div>
        <h1>{{ title }}</h1>
        <p>{{ description }}</p>
      </div>

      <div class="demo-page-badge">
        <span class="demo-page-badge__dot" />
        {{ badge }}
      </div>
    </header>

    <slot />
  </section>
</template>







<script setup lang="ts">
withDefaults(defineProps<{
  title: string
  description: string
  badge?: string
}>(), {
  badge: '示例数据',
})
</script>

<style lang="scss">
.demo-page-shell {
  min-height: 100%;
  padding: 14px 4px 36px;
  color: var(--app-text);
}

.demo-page-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 6px 0 22px;
  border-bottom: 1px solid var(--app-border);
}

.demo-page-kicker,
.demo-card-code {
  color: var(--el-color-primary);
  font-family: var(--app-mono);
  font-size: 11px;
  letter-spacing: .08em;
}

.demo-page-heading h1 {
  margin: 8px 0 6px;
  font-size: clamp(24px, 3vw, 34px);
  font-weight: 560;
  letter-spacing: -.03em;
  line-height: 1.15;
}


.demo-page-heading p {
  max-width: 720px;
  margin: 0;
  color: var(--app-muted);
  font-size: 13px;
  line-height: 1.6;
}

.demo-page-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
  padding: 7px 10px;
  border: 1px solid var(--app-border);
  color: var(--app-muted);
  font-family: var(--app-mono);
  font-size: 11px;
}

.demo-page-badge__dot {
  width: 7px;
  height: 7px;
  background: var(--el-color-primary);
}

.demo-card,
.demo-filter-card {
  border: 1px solid var(--app-border);
  border-radius: 2px;
  background: var(--app-surface);
}

.demo-filter-card {
  margin: 16px 0 12px;
}

.demo-filter-card :deep(.el-card__body) {
  padding: 14px 16px;
}

.demo-filter-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  align-items: end;
}

.demo-filter-grid .el-form-item {
  margin-bottom: 0;
}

.demo-filter-grid .el-form-item__label {
  color: var(--app-muted);
  font-size: 12px;
}

.demo-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 12px 0;
}

.demo-metric-card {
  min-height: 108px;
}

.demo-metric-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 76px;
}

.demo-metric-label,
.demo-metric-note,
.demo-card-note {
  color: var(--app-muted);
  font-size: 12px;
}

.demo-metric-value {
  display: block;
  margin: 10px 0 4px;
  color: var(--el-color-primary);
  font-size: 25px;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.demo-content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(320px, .9fr);
  gap: 12px;
  margin-top: 12px;
}

.demo-chart-card,
.demo-table-card {
  min-width: 0;
}

.demo-chart-card :deep(.el-card__header),
.demo-table-card :deep(.el-card__header) {
  padding: 13px 16px;
  border-bottom: 1px solid var(--app-border);
}

.demo-chart-card :deep(.el-card__body),
.demo-table-card :deep(.el-card__body) {
  padding: 12px 16px 16px;
}

.demo-card-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.demo-card-heading strong {
  font-size: 14px;
  font-weight: 600;
}

.demo-chart-card--wide {
  grid-column: 1 / -1;
}

.demo-chart-note {
  margin: 0 0 8px;
  color: var(--app-muted);
  font-size: 12px;
}

.demo-drilldown {
  display: flex;
  align-items: center;
  gap: 4px;
  min-height: 28px;
  margin-bottom: 4px;
  color: var(--app-muted);
  font-size: 12px;
}

.demo-drilldown__button {
  padding: 0 3px;
  border: 0;
  background: transparent;
  color: var(--el-color-primary);
  cursor: pointer;
  font: inherit;
}

.demo-drilldown__button:hover {
  text-decoration: underline;
}

.demo-drilldown__separator {
  color: var(--app-border);
}

.demo-table {
  width: 100%;
}

.demo-table code {
  color: var(--el-color-primary);
  font-family: var(--app-mono);
  font-size: 12px;
}

.demo-table .number-cell {
  font-variant-numeric: tabular-nums;
}

@media (max-width: 1100px) {

  .demo-filter-grid,
  .demo-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .demo-content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .demo-page-heading {
    flex-direction: column;
  }

  .demo-filter-grid,
  .demo-summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
