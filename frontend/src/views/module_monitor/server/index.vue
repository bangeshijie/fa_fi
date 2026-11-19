<template>
  <section class="monitor-page server-page">
    <header class="page-heading">
      <div>
        <div class="heading-title-row">
          <h2>服务器监控</h2>
          <p class="eyebrow">MONITOR / SERVER</p>
        </div>
        <p class="heading-copy">查看当前运行主机、Python 进程和磁盘资源的实时概况。</p>
      </div>
      <div class="heading-actions">
        <el-tag type="info" effect="plain">{{ lastUpdated ? `更新于 ${lastUpdated}` : '尚未采集' }}</el-tag>
        <el-switch v-model="autoRefresh" active-text="自动刷新" />
        <el-button :loading="loading" @click="loadData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </header>

    <el-row :gutter="12" class="summary-row">
      <el-col :xs="24" :sm="8">
        <el-card shadow="never" class="metric-card">
          <div class="metric-card-heading">
            <span class="summary-label">CPU 使用率</span>
            <el-icon><Cpu /></el-icon>
          </div>
          <div class="metric-body">
            <el-progress type="dashboard" :percentage="cpuUsage" :width="86" :color="progressColor(cpuUsage)" />
            <div>
              <strong>{{ currentServer.cpu.cpu_num }}</strong>
              <small>逻辑核心</small>
              <p>用户 {{ formatPercent(currentServer.cpu.used) }} · 系统 {{ formatPercent(currentServer.cpu.sys) }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="never" class="metric-card">
          <div class="metric-card-heading">
            <span class="summary-label">系统内存</span>
            <el-icon><DataLine /></el-icon>
          </div>
          <div class="metric-body">
            <el-progress type="dashboard" :percentage="memoryUsage" :width="86" :color="progressColor(memoryUsage)" />
            <div>
              <strong>{{ currentServer.mem.used }}</strong>
              <small>已使用 / {{ currentServer.mem.total }}</small>
              <p>可用 {{ currentServer.mem.free }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="never" class="metric-card">
          <div class="metric-card-heading">
            <span class="summary-label">Python 进程</span>
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="metric-body">
            <el-progress type="dashboard" :percentage="processMemoryUsage" :width="86" :color="progressColor(processMemoryUsage)" />
            <div>
              <strong>{{ currentServer.py.memory_used }}</strong>
              <small>进程内存占用</small>
              <p>{{ currentServer.py.name }} · {{ currentServer.py.version }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12" class="content-row">
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="content-card">
          <template #header>
            <div class="card-heading">
              <div><span class="section-index">01</span><strong>系统信息</strong></div>
              <el-icon><Monitor /></el-icon>
            </div>
          </template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="主机名称">{{ currentServer.sys.computer_name || '—' }}</el-descriptions-item>
            <el-descriptions-item label="服务器 IP">{{ currentServer.sys.computer_ip || '—' }}</el-descriptions-item>
            <el-descriptions-item label="操作系统">{{ currentServer.sys.os_name || '—' }}</el-descriptions-item>
            <el-descriptions-item label="系统架构">{{ currentServer.sys.os_arch || '—' }}</el-descriptions-item>
            <el-descriptions-item label="项目路径">
              <span class="breakable-text">{{ currentServer.sys.user_dir || '—' }}</span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="content-card">
          <template #header>
            <div class="card-heading">
              <div><span class="section-index">02</span><strong>Python 运行信息</strong></div>
              <span class="card-note">当前进程</span>
            </div>
          </template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="进程名称">{{ currentServer.py.name || '—' }}</el-descriptions-item>
            <el-descriptions-item label="Python 版本">{{ currentServer.py.version || '—' }}</el-descriptions-item>
            <el-descriptions-item label="启动时间">{{ currentServer.py.start_time || '—' }}</el-descriptions-item>
            <el-descriptions-item label="运行时长">{{ currentServer.py.run_time || '—' }}</el-descriptions-item>
            <el-descriptions-item label="解释器路径">
              <span class="breakable-text">{{ currentServer.py.home || '—' }}</span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="content-card disk-card">
      <template #header>
        <div class="card-heading">
          <div><span class="section-index">03</span><strong>磁盘使用情况</strong></div>
          <span class="card-note">{{ currentServer.disks.length }} 个挂载点</span>
        </div>
      </template>
      <el-table v-loading="loading" :data="currentServer.disks" border stripe class="data-table">
        <el-table-column prop="dir_name" label="挂载路径" min-width="180" show-overflow-tooltip>
          <template #default="{ row }"><code>{{ row.dir_name }}</code></template>
        </el-table-column>
        <el-table-column prop="sys_type_name" label="文件系统" width="120" show-overflow-tooltip />
        <el-table-column prop="type_name" label="磁盘类型" min-width="190" show-overflow-tooltip />
        <el-table-column label="使用率" min-width="230">
          <template #default="{ row }">
            <div class="disk-progress">
              <el-progress :percentage="safePercent(row.usage)" :color="progressColor(row.usage)" />
              <span>{{ formatPercent(row.usage) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="used" label="已用" width="110" align="right" />
        <el-table-column prop="free" label="可用" width="110" align="right" />
        <el-table-column prop="total" label="总容量" width="110" align="right" />
      </el-table>
      <el-empty v-if="!loading && !currentServer.disks.length" description="暂无磁盘信息" />
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Cpu, DataLine, Monitor, Refresh } from '@element-plus/icons-vue'

import ServerAPI, { type ServerInfo } from '@/api/module_monitor/server'
import { useAsyncLoading, usePolling } from '@/hooks'

defineOptions({ name: 'MonitorServer' })

const emptyServer: ServerInfo = {
  cpu: { cpu_num: 0, used: 0, sys: 0, free: 0 },
  mem: { total: '—', used: '—', free: '—', usage: 0 },
  sys: { computer_ip: '', computer_name: '', os_arch: '', os_name: '', user_dir: '' },
  py: { name: '', version: '', start_time: '', run_time: '', home: '', memory_total: '—', memory_used: '—', memory_free: '—', memory_usage: 0 },
  disks: [],
}

const server = ref<ServerInfo>()
const lastUpdated = ref('')
const autoRefresh = ref(true)
const { loading, run } = useAsyncLoading()

const currentServer = computed(() => server.value || emptyServer)
const cpuUsage = computed(() => safePercent(100 - currentServer.value.cpu.free))
const memoryUsage = computed(() => safePercent(currentServer.value.mem.usage))
const processMemoryUsage = computed(() => safePercent(currentServer.value.py.memory_usage))

function safePercent(value: number | undefined) {
  return Math.round(Math.min(100, Math.max(0, Number(value) || 0)) * 10) / 10
}

function formatPercent(value: number | undefined) {
  return `${safePercent(value).toFixed(1)}%`
}

function progressColor(value: number) {
  if (value >= 85) return '#f56c6c'
  if (value >= 65) return '#e6a23c'
  return '#2f6fed'
}

async function loadData() {
  await run(async () => {
    const response = await ServerAPI.getServer()
    server.value = response.data.data
    lastUpdated.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  })
}

const { start: startRefresh } = usePolling(loadData, { interval: 30_000, enabled: autoRefresh })
onMounted(async () => {
  await loadData()
  startRefresh()
})
</script>

<style scoped lang="scss">
.monitor-page { min-height: 100%; padding: 14px 4px 36px; color: var(--app-text); }
.page-heading, .card-heading, .heading-actions, .metric-card-heading, .metric-body, .disk-progress { display: flex; align-items: center; }
.page-heading { justify-content: space-between; gap: 24px; padding: 6px 0 24px; border-bottom: 1px solid var(--app-border); }
.eyebrow, .section-index { margin: 0; color: var(--el-color-primary); font-size: 11px; font-weight: 700; letter-spacing: .12em; }
.heading-copy, .card-note, .summary-label, .metric-body small, .metric-body p { color: var(--app-muted); }
.heading-copy { margin: 12px 0 0; font-size: 13px; }
.heading-actions { flex-wrap: wrap; justify-content: flex-end; gap: 12px; }
.summary-row, .content-row { margin: 16px 0 0; }
.metric-card { min-height: 164px; }
.metric-card-heading { justify-content: space-between; color: var(--el-color-primary); }
.metric-body { gap: 18px; margin-top: 12px; }
.metric-body strong { display: block; color: var(--app-text); font-size: 24px; line-height: 1.1; font-variant-numeric: tabular-nums; }
.metric-body small { display: block; margin-top: 5px; font-size: 11px; }
.metric-body p { margin: 10px 0 0; font-size: 12px; }
.content-card { margin-top: 16px; }
.card-heading { justify-content: space-between; gap: 16px; }
.card-heading > div { display: flex; align-items: center; gap: 10px; }
.data-table { width: 100%; }
.breakable-text { word-break: break-all; }
code { color: var(--el-color-primary); font-family: var(--app-mono); font-size: 12px; }
.disk-progress { gap: 12px; }
.disk-progress :deep(.el-progress) { flex: 1; }
.disk-progress > span { width: 54px; color: var(--app-muted); font-size: 12px; text-align: right; font-variant-numeric: tabular-nums; }
@media (max-width: 760px) {
  .page-heading { align-items: flex-start; flex-direction: column; }
  .heading-actions { justify-content: flex-start; }
}
</style>
