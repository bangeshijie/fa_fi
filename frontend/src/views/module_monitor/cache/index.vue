<template>
  <section class="monitor-page cache-page">
    <header class="page-heading">
      <div>
        <div class="heading-title-row">
          <h2>缓存监控</h2>
          <p class="eyebrow">MONITOR / CACHE</p>
        </div>
        <p class="heading-copy">查看 Redis 运行状态、系统缓存命名空间和当前键值。</p>
      </div>
      <div class="heading-actions">
        <el-tag :type="redisOnline ? 'success' : 'danger'" effect="plain">
          {{ redisOnline ? 'Redis 已连接' : 'Redis 未连接' }}
        </el-tag>
        <el-button :loading="loading" @click="loadData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button v-permission="'module_monitor:cache:delete'" type="danger" plain @click="handleClearAll">
          <el-icon><Delete /></el-icon>
          清空系统缓存
        </el-button>
      </div>
    </header>

    <el-row :gutter="12" class="summary-row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">数据库键数</span>
          <strong>{{ cacheInfo?.db_size ?? 0 }}</strong>
          <small>当前 Redis DB</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">已用内存</span>
          <strong>{{ infoValue('used_memory_human', '—') }}</strong>
          <small>{{ infoValue('redis_version', 'Redis') }}</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">连接客户端</span>
          <strong>{{ infoValue('connected_clients', 0) }}</strong>
          <small>当前连接数</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">运行天数</span>
          <strong>{{ infoValue('uptime_in_days', 0) }}</strong>
          <small>Redis uptime</small>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12" class="content-row">
      <el-col :xs="24" :lg="9">
        <el-card shadow="never" class="content-card namespace-card">
          <template #header>
            <div class="card-heading">
              <div><span class="section-index">01</span><strong>缓存命名空间</strong></div>
              <span class="card-note">{{ cacheNames.length }} 个系统前缀</span>
            </div>
          </template>

          <el-table
            v-loading="loading"
            :data="cacheNames"
            row-key="cache_name"
            highlight-current-row
            class="data-table"
            @row-click="handleSelectNamespace"
          >
            <el-table-column label="缓存名称" min-width="170">
              <template #default="{ row }">
                <div class="namespace-name">
                  <span class="namespace-mark" />
                  <code>{{ row.cache_name }}</code>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="remark" label="说明" min-width="145" show-overflow-tooltip />
            <el-table-column label="操作" width="80" align="center">
              <template #default="{ row }">
                <el-button
                  v-permission="'module_monitor:cache:delete'"
                  link
                  type="danger"
                  @click.stop="handleClearNamespace(row.cache_name)"
                >
                  清除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!loading && !cacheNames.length" description="暂无缓存命名空间" />
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="15">
        <el-card shadow="never" class="content-card key-card">
          <template #header>
            <div class="card-heading">
              <div><span class="section-index">02</span><strong>缓存键</strong></div>
              <code v-if="selectedCacheName">{{ selectedCacheName }}:*</code>
              <span v-else class="card-note">请选择命名空间</span>
            </div>
          </template>

          <div class="key-toolbar">
            <el-input
              v-model="keyKeyword"
              clearable
              :disabled="!selectedCacheName"
              placeholder="筛选当前命名空间的键"
            >
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button :disabled="!selectedCacheName" :loading="keyLoading" @click="loadKeys(selectedCacheName)">
              <el-icon><Refresh /></el-icon>
              刷新键
            </el-button>
          </div>

          <el-table v-loading="keyLoading" :data="filteredKeys" class="data-table key-table">
            <el-table-column type="index" label="#" width="58" align="center" />
            <el-table-column label="键名" min-width="260" show-overflow-tooltip>
              <template #default="{ row }"><code>{{ row }}</code></template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right" align="center">
              <template #default="{ row }">
                <el-button link type="primary" @click="openValue(row)">
                  <el-icon><View /></el-icon>
                  查看值
                </el-button>
                <el-button
                  v-permission="'module_monitor:cache:delete'"
                  link
                  type="danger"
                  @click="handleDeleteKey(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty
            v-if="!keyLoading && selectedCacheName && !filteredKeys.length"
            description="当前命名空间暂无匹配的键"
          />
          <el-empty v-if="!selectedCacheName" description="请先选择左侧缓存命名空间" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12" class="content-row">
      <el-col :xs="24" :lg="14">
        <el-card shadow="never" class="content-card">
          <template #header>
            <div class="card-heading">
              <div><span class="section-index">03</span><strong>命令统计</strong></div>
              <span class="card-note">按调用次数降序</span>
            </div>
          </template>
          <el-table :data="cacheInfo?.command_stats || []" class="data-table command-table">
            <el-table-column type="index" label="#" width="58" align="center" />
            <el-table-column prop="name" label="命令" min-width="180">
              <template #default="{ row }"><code>{{ row.name }}</code></template>
            </el-table-column>
            <el-table-column prop="value" label="调用次数" width="140" align="right" />
          </el-table>
          <el-empty v-if="!cacheInfo?.command_stats?.length" description="暂无命令统计" />
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="10">
        <el-card shadow="never" class="content-card info-card">
          <template #header>
            <div class="card-heading">
              <div><span class="section-index">04</span><strong>Redis 信息</strong></div>
              <span class="card-note">INFO server</span>
            </div>
          </template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="版本">{{ infoValue('redis_version', '—') }}</el-descriptions-item>
            <el-descriptions-item label="运行模式">{{ infoValue('redis_mode', '—') }}</el-descriptions-item>
            <el-descriptions-item label="端口">{{ infoValue('tcp_port', '—') }}</el-descriptions-item>
            <el-descriptions-item label="AOF">{{ infoValue('aof_enabled', '—') }}</el-descriptions-item>
            <el-descriptions-item label="RDB 状态">{{ infoValue('rdb_last_bgsave_status', '—') }}</el-descriptions-item>
            <el-descriptions-item label="输入速率">{{ infoValue('instantaneous_input_kbps', '—') }} KB/s</el-descriptions-item>
            <el-descriptions-item label="输出速率">{{ infoValue('instantaneous_output_kbps', '—') }} KB/s</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="valueVisible" title="缓存值" width="720px" destroy-on-close>
      <div v-loading="valueLoading" class="value-dialog">
        <div class="value-meta">
          <span>{{ valueRecord?.cache_name || selectedCacheName }}</span>
          <code>{{ valueRecord?.cache_key || '—' }}</code>
        </div>
        <pre v-if="valueRecord">{{ formatValue(valueRecord.cache_value) }}</pre>
        <el-empty v-else-if="!valueLoading" description="缓存值不存在或为空" />
      </div>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Delete, Refresh, Search, View } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import CacheAPI, { type CacheInfo, type CacheMonitor } from '@/api/module_monitor/cache'

defineOptions({ name: 'MonitorCache' })

const loading = ref(false)
const keyLoading = ref(false)
const valueLoading = ref(false)
const cacheInfo = ref<CacheMonitor>()
const cacheNames = ref<CacheInfo[]>([])
const cacheKeys = ref<string[]>([])
const selectedCacheName = ref('')
const keyKeyword = ref('')
const valueVisible = ref(false)
const valueRecord = ref<CacheInfo>()

const redisOnline = computed(() => Boolean(cacheInfo.value?.info?.redis_version))
const filteredKeys = computed(() => {
  const keyword = keyKeyword.value.trim().toLowerCase()
  return keyword ? cacheKeys.value.filter((key) => key.toLowerCase().includes(keyword)) : cacheKeys.value
})

function infoValue(key: string, fallback: string | number) {
  return cacheInfo.value?.info?.[key] ?? fallback
}

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === '') return '（空值）'
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}

async function loadKeys(cacheName: string) {
  if (!cacheName) return
  keyLoading.value = true
  try {
    const response = await CacheAPI.getCacheKeys(cacheName)
    cacheKeys.value = response.data.data || []
  } finally {
    keyLoading.value = false
  }
}

async function loadData() {
  loading.value = true
  try {
    const [infoResponse, namesResponse] = await Promise.all([CacheAPI.getCacheInfo(), CacheAPI.getCacheNames()])
    cacheInfo.value = infoResponse.data.data
    cacheNames.value = namesResponse.data.data || []

    const hasSelected = cacheNames.value.some((item) => item.cache_name === selectedCacheName.value)
    if (!hasSelected) selectedCacheName.value = cacheNames.value[0]?.cache_name || ''
    cacheKeys.value = []
    keyKeyword.value = ''
    if (selectedCacheName.value) await loadKeys(selectedCacheName.value)
  } finally {
    loading.value = false
  }
}

async function handleSelectNamespace(row: CacheInfo) {
  if (row.cache_name === selectedCacheName.value) return
  selectedCacheName.value = row.cache_name
  keyKeyword.value = ''
  await loadKeys(row.cache_name)
}

async function openValue(cacheKey: string) {
  if (!selectedCacheName.value) return
  valueVisible.value = true
  valueLoading.value = true
  valueRecord.value = undefined
  try {
    const response = await CacheAPI.getCacheValue(selectedCacheName.value, cacheKey)
    valueRecord.value = response.data.data
  } finally {
    valueLoading.value = false
  }
}

async function handleClearNamespace(cacheName: string) {
  try {
    await ElMessageBox.confirm(`确定清除“${cacheName}”下的全部缓存吗？`, '清除缓存', {
      type: 'warning',
      confirmButtonText: '确定清除',
      cancelButtonText: '取消',
    })
    await CacheAPI.deleteCacheName(cacheName)
    ElMessage.success('命名空间缓存已清除')
    await loadData()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    throw error
  }
}

async function handleDeleteKey(cacheKey: string) {
  if (!selectedCacheName.value) return
  try {
    await ElMessageBox.confirm(`确定删除缓存键“${selectedCacheName.value}:${cacheKey}”吗？`, '删除缓存键', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })
    await CacheAPI.deleteCacheKey(selectedCacheName.value, cacheKey)
    ElMessage.success('缓存键已删除')
    await loadData()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    throw error
  }
}

async function handleClearAll() {
  try {
    await ElMessageBox.confirm('只清除系统登记的缓存命名空间，不影响 Redis 中的其他业务键。确定继续吗？', '清空系统缓存', {
      type: 'warning',
      confirmButtonText: '确定清空',
      cancelButtonText: '取消',
    })
    await CacheAPI.deleteCacheAll()
    ElMessage.success('系统缓存已清空')
    await loadData()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    throw error
  }
}

onMounted(loadData)
</script>

<style scoped lang="scss">
.monitor-page { min-height: 100%; padding: 14px 4px 36px; color: var(--app-text); }
.page-heading, .card-heading, .heading-actions, .key-toolbar, .namespace-name, .value-meta { display: flex; align-items: center; }
.page-heading { justify-content: space-between; gap: 24px; padding: 6px 0 24px; border-bottom: 1px solid var(--app-border); }
.eyebrow, .section-index { margin: 0; color: var(--el-color-primary); font-size: 11px; font-weight: 700; letter-spacing: .12em; }
.heading-copy, .card-note, .summary-label, .summary-card small { color: var(--app-muted); }
.heading-copy { margin: 12px 0 0; font-size: 13px; }
.heading-actions { flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
.summary-row, .content-row { margin: 16px 0 0; }
.summary-card { min-height: 112px; }
.summary-label, .summary-card small { display: block; }
.summary-label { font-size: 12px; }
.summary-card strong { display: block; margin: 8px 0 4px; color: var(--el-color-primary); font-size: 30px; line-height: 1; font-variant-numeric: tabular-nums; }
.summary-card small { font-size: 11px; }
.content-card { margin-top: 16px; }
.card-heading { justify-content: space-between; gap: 16px; }
.card-heading > div { display: flex; align-items: center; gap: 10px; }
.data-table { width: 100%; }
.namespace-name { gap: 9px; }
.namespace-mark { width: 7px; height: 7px; border-radius: 50%; background: var(--el-color-primary); }
code, pre { font-family: var(--app-mono); }
code { color: var(--el-color-primary); font-size: 12px; }
.key-toolbar { gap: 10px; margin-bottom: 12px; }
.key-toolbar .el-input { max-width: 420px; }
.key-table { min-height: 180px; }
.command-table { min-height: 220px; }
.info-card :deep(.el-descriptions__label) { width: 112px; }
.value-dialog { min-height: 160px; }
.value-meta { justify-content: space-between; gap: 12px; margin-bottom: 12px; color: var(--app-muted); font-size: 12px; }
.value-meta code { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.value-dialog pre { max-height: 460px; margin: 0; padding: 14px; overflow: auto; color: var(--app-text); background: var(--app-surface-muted); border: 1px solid var(--app-border); border-radius: 4px; white-space: pre-wrap; word-break: break-word; }
@media (max-width: 760px) {
  .page-heading { align-items: flex-start; flex-direction: column; }
  .heading-actions { justify-content: flex-start; }
  .key-toolbar { align-items: stretch; flex-direction: column; }
  .key-toolbar .el-input { max-width: none; }
  .value-meta { align-items: flex-start; flex-direction: column; }
}
</style>
