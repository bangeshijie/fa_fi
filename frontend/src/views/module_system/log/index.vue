<template>
  <section class="log-page">
    <header class="page-heading">
      <div>
        <div class="heading-title-row">
          <h2>系统日志</h2>
          <p class="eyebrow">SYSTEM / LOG</p>
        </div>
        <p class="heading-copy">查询登录与操作记录，定位请求来源、响应结果和处理耗时。</p>
      </div>
      <div class="heading-actions">
        <el-tag type="info" effect="plain">审计记录</el-tag>
        <el-button :loading="loading" @click="loadData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button v-permission="'module_system:log:export'" type="primary" plain :loading="exporting"
          @click="handleExport">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
        <el-button v-permission="'module_system:log:delete'" type="danger" plain :disabled="!selectedIds.length"
          @click="handleBatchDelete">
          <el-icon><Delete /></el-icon>
          删除所选
        </el-button>
      </div>
    </header>

    <el-row :gutter="12" class="summary-row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">记录总数</span>
          <strong>{{ total }}</strong>
          <small>符合筛选条件</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">登录日志</span>
          <strong>{{ loginCount }}</strong>
          <small>当前页记录</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">操作日志</span>
          <strong>{{ operationCount }}</strong>
          <small>当前页记录</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">异常响应</span>
          <strong>{{ errorCount }}</strong>
          <small>当前页非 2xx 响应</small>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="content-card">
      <template #header>
        <div class="card-heading">
          <div>
            <span class="section-index">01</span>
            <strong>日志列表</strong>
          </div>
          <span class="card-note">详情权限独立控制</span>
        </div>
      </template>

      <el-form :inline="true" class="search-bar" @submit.prevent="handleSearch">
        <el-form-item label="日志类型">
          <el-select v-model="query.type" clearable placeholder="全部类型" class="filter-select">
            <el-option :value="1" label="登录日志" />
            <el-option :value="2" label="操作日志" />
          </el-select>
        </el-form-item>
        <el-form-item label="请求路径">
          <el-input v-model="query.request_path" clearable placeholder="例如 /api/v1/system/user/list" />
        </el-form-item>
        <el-form-item label="请求方法">
          <el-select v-model="query.request_method" clearable placeholder="全部方法" class="method-select">
            <el-option v-for="method in requestMethods" :key="method" :value="method" :label="method" />
          </el-select>
        </el-form-item>
        <el-form-item label="IP 地址">
          <el-input v-model="query.request_ip" clearable placeholder="请输入 IP" />
        </el-form-item>
        <el-form-item label="响应码">
          <el-select v-model="query.response_code" clearable placeholder="全部响应" class="method-select">
            <el-option v-for="code in responseCodes" :key="code" :value="code" :label="String(code)" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="query.description" clearable placeholder="请输入日志描述" />
        </el-form-item>
        <el-form-item label="创建时间">
          <el-date-picker v-model="query.created_time" type="datetimerange" value-format="YYYY-MM-DD HH:mm:ss"
            start-placeholder="开始时间" end-placeholder="结束时间" range-separator="至" class="date-range" />
        </el-form-item>
        <el-form-item class="search-actions">
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="rows" border stripe class="log-table" row-key="id"
        @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="48" fixed="left" />
        <el-table-column type="index" label="#" width="58" align="center" />
        <el-table-column prop="created_time" label="时间" width="178" show-overflow-tooltip />
        <el-table-column label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.type === 1 ? 'warning' : 'primary'" effect="plain" size="small">
              {{ row.type === 1 ? '登录日志' : '操作日志' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip />
        <el-table-column prop="request_path" label="请求路径" min-width="230" show-overflow-tooltip />
        <el-table-column label="方法" width="86" align="center">
          <template #default="{ row }">
            <span class="method-code">{{ row.request_method || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="request_ip" label="IP 地址" width="142" show-overflow-tooltip />
        <el-table-column label="响应" width="88" align="center">
          <template #default="{ row }">
            <el-tag :type="responseTagType(row.response_code)" effect="plain" size="small">
              {{ row.response_code || '—' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="process_time" label="耗时" width="100" show-overflow-tooltip />
        <el-table-column label="操作人" width="110" show-overflow-tooltip>
          <template #default="{ row }">{{ row.created_by?.name || '系统' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <el-button v-permission="'module_system:log:detail'" link type="primary" @click="handleDetail(row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
            <el-button v-permission="'module_system:log:delete'" link type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-row">
        <el-pagination v-model:current-page="query.page_no" v-model:page-size="query.page_size" :total="total"
          :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next, jumper" @change="loadData" />
      </div>
    </el-card>

    <el-drawer v-model="detailVisible" title="日志详情" size="680px" destroy-on-close>
      <el-empty v-if="!detail" description="暂无详情" />
      <template v-else>
        <el-descriptions :column="2" border class="detail-descriptions">
          <el-descriptions-item label="日志 ID">{{ detail.id || '—' }}</el-descriptions-item>
          <el-descriptions-item label="日志类型">{{ detail.type === 1 ? '登录日志' : '操作日志' }}</el-descriptions-item>
          <el-descriptions-item label="请求方法">{{ detail.request_method || '—' }}</el-descriptions-item>
          <el-descriptions-item label="响应码">{{ detail.response_code || '—' }}</el-descriptions-item>
          <el-descriptions-item label="请求路径" :span="2">{{ detail.request_path || '—' }}</el-descriptions-item>
          <el-descriptions-item label="请求 IP">{{ detail.request_ip || '—' }}</el-descriptions-item>
          <el-descriptions-item label="处理耗时">{{ detail.process_time || '—' }}</el-descriptions-item>
          <el-descriptions-item label="登录位置">{{ detail.login_location || '—' }}</el-descriptions-item>
          <el-descriptions-item label="操作人">{{ detail.created_by?.name || '系统' }}</el-descriptions-item>
          <el-descriptions-item label="操作系统">{{ detail.request_os || '—' }}</el-descriptions-item>
          <el-descriptions-item label="浏览器">{{ detail.request_browser || '—' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">{{ detail.created_time || '—' }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ detail.description || '—' }}</el-descriptions-item>
        </el-descriptions>

        <div class="payload-block">
          <div class="payload-heading">REQUEST PAYLOAD</div>
          <pre>{{ formatJson(detail.request_payload) }}</pre>
        </div>
        <div class="payload-block">
          <div class="payload-heading">RESPONSE JSON</div>
          <pre>{{ formatJson(detail.response_json) }}</pre>
        </div>
      </template>
    </el-drawer>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Delete, Download, Refresh, Search, View } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import LogAPI, { type LogPageQuery, type LogTable } from '@/api/module_system/log'
import download from '@/utils/download'

defineOptions({ name: 'Log' })

const requestMethods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
const responseCodes = [200, 201, 204, 400, 401, 403, 404, 422, 500]
const loading = ref(false)
const exporting = ref(false)
const rows = ref<LogTable[]>([])
const total = ref(0)
const selectedIds = ref<number[]>([])
const detailVisible = ref(false)
const detail = ref<LogTable>()
const query = reactive<LogPageQuery>({ page_no: 1, page_size: 10 })

const loginCount = computed(() => rows.value.filter((row) => row.type === 1).length)
const operationCount = computed(() => rows.value.filter((row) => row.type === 2).length)
const errorCount = computed(() => rows.value.filter((row) => !row.response_code || row.response_code < 200 || row.response_code >= 300).length)

async function loadData() {
  loading.value = true
  try {
    const response = await LogAPI.listLog({ ...query })
    const result = response.data.data
    rows.value = result?.items || []
    total.value = result?.total || 0
    selectedIds.value = []
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  query.page_no = 1
  return loadData()
}

function handleReset() {
  query.type = undefined
  query.request_path = undefined
  query.request_method = undefined
  query.request_ip = undefined
  query.response_code = undefined
  query.description = undefined
  query.created_time = undefined
  query.page_no = 1
  return loadData()
}

function handleSelectionChange(selection: LogTable[]) {
  selectedIds.value = selection.map((row) => row.id).filter((id): id is number => typeof id === 'number')
}

async function handleDelete(row: LogTable) {
  if (!row.id) return
  await ElMessageBox.confirm('删除后将无法恢复，确定删除这条日志吗？', '删除日志', {
    type: 'warning',
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
  })
  await LogAPI.deleteLog([row.id])
  ElMessage.success('日志已删除')
  await loadData()
}

async function handleBatchDelete() {
  if (!selectedIds.value.length) return
  await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 条日志吗？`, '批量删除日志', {
    type: 'warning',
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
  })
  await LogAPI.deleteLog(selectedIds.value)
  ElMessage.success('选中日志已删除')
  await loadData()
}

async function handleDetail(row: LogTable) {
  if (!row.id) return
  const response = await LogAPI.detailLog(row.id)
  detail.value = response.data.data
  detailVisible.value = true
}

async function handleExport() {
  exporting.value = true
  try {
    const response = await LogAPI.exportLog({ ...query })
    download.saveAs(response.data, `system-log-${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('日志导出成功')
  } finally {
    exporting.value = false
  }
}

function responseTagType(code?: number) {
  if (!code) return 'info'
  if (code >= 200 && code < 300) return 'success'
  if (code >= 400) return 'danger'
  return 'warning'
}

function formatJson(value?: string) {
  if (!value) return '—'
  try {
    return JSON.stringify(JSON.parse(value), null, 2)
  } catch {
    return value
  }
}

onMounted(loadData)
</script>

<style scoped lang="scss">
.log-page {
  min-height: 100%;
  padding: 14px 4px 36px;
  color: var(--app-text);
}

.page-heading,
.card-heading,
.heading-actions,
.pagination-row {
  display: flex;
  align-items: center;
}

.page-heading {
  justify-content: space-between;
  gap: 24px;
  padding: 6px 0 24px;
  border-bottom: 1px solid var(--app-border);
}

.eyebrow,
.section-index {
  margin: 0;
  color: var(--el-color-primary);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .12em;
}

.heading-copy,
.card-note {
  color: var(--app-muted);
}

.heading-copy {
  margin: 12px 0 0;
  font-size: 13px;
}

.heading-actions {
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.summary-row {
  margin: 16px 0;
}

.summary-card {
  min-height: 112px;
}

.summary-label,
.summary-card small {
  display: block;
  color: var(--app-muted);
}

.summary-label {
  font-size: 12px;
}

.summary-card strong {
  display: block;
  margin: 8px 0 4px;
  color: var(--el-color-primary);
  font-size: 30px;
  line-height: 1;
}

.summary-card small {
  font-size: 11px;
}

.content-card {
  margin-top: 16px;
}

.card-heading {
  justify-content: space-between;
  gap: 16px;
}

.card-heading > div {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0 12px;
  margin-bottom: 4px;
}

.filter-select {
  width: 132px;
}

.method-select {
  width: 112px;
}

.date-range {
  width: 350px;
}

.method-code {
  color: var(--el-color-primary);
  font-family: var(--app-mono, ui-monospace, monospace);
  font-size: 12px;
  font-weight: 700;
}

.pagination-row {
  justify-content: flex-end;
  padding-top: 16px;
}

.payload-block {
  margin-top: 22px;
}

.payload-heading {
  margin-bottom: 8px;
  color: var(--el-color-primary);
  font-family: var(--app-mono, ui-monospace, monospace);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .1em;
}

pre {
  max-height: 260px;
  margin: 0;
  overflow: auto;
  padding: 14px;
  border: 1px solid var(--app-border);
  background: var(--app-surface-muted, var(--el-fill-color-light));
  color: var(--app-text);
  font: 12px/1.6 var(--app-mono, ui-monospace, monospace);
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 760px) {
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .heading-actions {
    justify-content: flex-start;
  }

  .date-range {
    width: min(350px, 100%);
  }
}
</style>
