<template>
  <section class="monitor-page resource-page">
    <header class="page-heading">
      <div>
        <p class="eyebrow">MONITOR / RESOURCE</p>
        <h1>文件管理</h1>
        <p class="heading-copy">管理系统 upload 目录中的文件和目录，操作范围受后端路径校验保护。</p>
      </div>
      <div class="heading-actions">
        <el-tag type="info" effect="plain">当前目录：{{ currentPathLabel }}</el-tag>
        <el-button :loading="loading" @click="loadData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button v-permission="'module_monitor:resource:export'" type="primary" plain :loading="exporting" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出列表
        </el-button>
        <el-button v-permission="'module_monitor:resource:create_dir'" type="primary" plain @click="openCreateDirectory">
          <el-icon><FolderAdd /></el-icon>
          新建目录
        </el-button>
        <el-button v-permission="'module_monitor:resource:upload'" type="primary" @click="openFilePicker">
          <el-icon><Upload /></el-icon>
          上传文件
        </el-button>
        <input ref="fileInput" class="hidden-input" type="file" @change="handleFileChange" />
      </div>
    </header>

    <el-row :gutter="12" class="summary-row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">目录条目</span>
          <strong>{{ total }}</strong>
          <small>当前目录全部条目</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">当前页文件</span>
          <strong>{{ currentFileCount }}</strong>
          <small>文件资源</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">当前页目录</span>
          <strong>{{ currentDirectoryCount }}</strong>
          <small>可进入目录</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">已选条目</span>
          <strong>{{ selectedPaths.length }}</strong>
          <small>可批量删除</small>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="content-card">
      <template #header>
        <div class="card-heading">
          <div><span class="section-index">01</span><strong>资源列表</strong></div>
          <div class="card-heading-actions">
            <span class="card-note">{{ uploading ? '正在上传文件…' : '仅显示当前目录' }}</span>
            <el-button v-permission="'module_monitor:resource:delete'" text type="danger" :disabled="!selectedPaths.length" @click="handleBatchDelete">
              <el-icon><Delete /></el-icon>
              删除所选
            </el-button>
          </div>
        </div>
      </template>

      <div class="path-bar">
        <span class="path-label">路径</span>
        <el-button text type="primary" @click="goRoot">upload</el-button>
        <template v-for="(part, index) in pathParts" :key="`${part}-${index}`">
          <span class="path-separator">/</span>
          <el-button text type="primary" @click="goPath(index)">{{ part }}</el-button>
        </template>
      </div>

      <el-form :inline="true" class="search-bar" @submit.prevent="handleSearch">
        <el-form-item label="文件名">
          <el-input v-model="query.name" clearable placeholder="搜索当前目录文件名" @keyup.enter="handleSearch">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item class="search-actions">
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="rows" border stripe row-key="relative_path" class="data-table" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="48" fixed="left" />
        <el-table-column type="index" label="#" width="58" align="center" />
        <el-table-column label="名称" min-width="250" fixed="left" show-overflow-tooltip>
          <template #default="{ row }">
            <button v-if="row.is_dir" type="button" class="name-link" @click="enterDirectory(row)">
              <el-icon><FolderOpened /></el-icon>
              <span>{{ row.name }}</span>
            </button>
            <div v-else class="resource-name">
              <el-icon><Document /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_dir ? 'warning' : 'primary'" effect="plain" size="small">
              {{ row.is_dir ? '目录' : '文件' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="110" align="right">
          <template #default="{ row }">{{ row.is_file ? formatSize(row.size) : '—' }}</template>
        </el-table-column>
        <el-table-column prop="relative_path" label="相对路径" min-width="220" show-overflow-tooltip>
          <template #default="{ row }"><code>{{ row.relative_path || '—' }}</code></template>
        </el-table-column>
        <el-table-column prop="modified_time" label="修改时间" width="178" show-overflow-tooltip>
          <template #default="{ row }">{{ formatDateTime(row.modified_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="190" fixed="right" align="center">
          <template #default="{ row }">
            <el-button v-if="row.is_file" v-permission="'module_monitor:resource:download'" link type="primary" @click="handleDownload(row)">
              <el-icon><Download /></el-icon>
              下载
            </el-button>
            <el-dropdown trigger="click">
              <el-button link type="primary">
                更多<el-icon class="el-icon--right"><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item v-permission="'module_monitor:resource:rename'" @click="openRename(row)">
                    <el-icon><Edit /></el-icon>重命名
                  </el-dropdown-item>
                  <el-dropdown-item v-permission="'module_monitor:resource:move'" @click="openTransfer(row, 'move')">
                    移动
                  </el-dropdown-item>
                  <el-dropdown-item v-permission="'module_monitor:resource:copy'" @click="openTransfer(row, 'copy')">
                    复制
                  </el-dropdown-item>
                  <el-dropdown-item v-permission="'module_monitor:resource:delete'" divided @click="handleDelete([row])">
                    <span class="danger-text">删除</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !rows.length" description="当前目录暂无资源" />

      <div class="pagination-row">
        <el-pagination v-model:current-page="query.page_no" v-model:page-size="query.page_size" :total="total" :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next, jumper" @change="loadData" />
      </div>
    </el-card>

    <el-dialog v-model="createDirectoryVisible" title="新建目录" width="520px" destroy-on-close>
      <el-form ref="createDirectoryFormRef" :model="createDirectoryForm" :rules="createDirectoryRules" label-width="92px">
        <el-form-item label="父目录">
          <code>{{ currentPathLabel }}</code>
        </el-form-item>
        <el-form-item label="目录名称" prop="dir_name">
          <el-input v-model="createDirectoryForm.dir_name" maxlength="255" show-word-limit placeholder="请输入目录名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDirectoryVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreateDirectory">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="operationVisible" :title="operationTitle" width="560px" destroy-on-close>
      <el-form :model="operationForm" label-width="112px">
        <el-form-item v-if="operationType === 'rename'" label="原路径">
          <code class="path-value">{{ operationForm.old_path }}</code>
        </el-form-item>
        <el-form-item v-if="operationType === 'rename'" label="新名称">
          <el-input v-model="operationForm.new_name" maxlength="255" placeholder="请输入新的文件或目录名称" />
        </el-form-item>
        <el-form-item v-else label="源路径">
          <code class="path-value">{{ operationForm.source_path }}</code>
        </el-form-item>
        <el-form-item v-if="operationType !== 'rename'" label="目标路径">
          <el-input v-model="operationForm.target_path" placeholder="请输入目标路径（包含文件名）" />
        </el-form-item>
        <el-form-item v-if="operationType !== 'rename'" label="目标已存在">
          <el-switch v-model="operationForm.overwrite" active-text="覆盖" inactive-text="拒绝" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="operationVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleOperation">确定</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Delete, Document, Download, Edit, FolderAdd, FolderOpened, MoreFilled, Refresh, Search, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'

import ResourceAPI, {
  type ResourceCreateDirQuery,
  type ResourceItem,
  type ResourceMoveQuery,
  type ResourcePageQuery,
  type ResourceRenameQuery,
} from '@/api/module_monitor/resource'
import { useAsyncLoading } from '@/hooks'
import download from '@/utils/download'

defineOptions({ name: 'MonitorResource' })

const uploading = ref(false)
const exporting = ref(false)
const submitting = ref(false)
const rows = ref<ResourceItem[]>([])
const total = ref(0)
const selectedPaths = ref<string[]>([])
const fileInput = ref<HTMLInputElement>()
const createDirectoryVisible = ref(false)
const createDirectoryFormRef = ref<FormInstance>()
const operationVisible = ref(false)
const operationType = ref<'rename' | 'move' | 'copy'>('rename')
const { loading, run } = useAsyncLoading()

const query = reactive<ResourcePageQuery>({ page_no: 1, page_size: 10 })
const createDirectoryForm = reactive<ResourceCreateDirQuery>({ parent_path: '', dir_name: '' })
const operationForm = reactive({ old_path: '', new_name: '', source_path: '', target_path: '', overwrite: false })

const createDirectoryRules: FormRules<ResourceCreateDirQuery> = {
  dir_name: [{ required: true, message: '请输入目录名称', trigger: 'blur' }],
}

const pathParts = computed(() => (query.path ? query.path.split('/').filter(Boolean) : []))
const currentPathLabel = computed(() => query.path || 'upload')
const currentFileCount = computed(() => rows.value.filter((row) => row.is_file).length)
const currentDirectoryCount = computed(() => rows.value.filter((row) => row.is_dir).length)
const operationTitle = computed(() => ({ rename: '重命名', move: '移动资源', copy: '复制资源' })[operationType.value])

async function loadData() {
  await run(async () => {
    const response = await ResourceAPI.listResource({ ...query })
    const result = response.data.data
    rows.value = result?.items || []
    total.value = result?.total || 0
    selectedPaths.value = []
  })
}

function handleSearch() {
  query.page_no = 1
  return loadData()
}

function handleReset() {
  query.name = undefined
  query.page_no = 1
  return loadData()
}

function handleSelectionChange(selection: ResourceItem[]) {
  selectedPaths.value = selection.map((row) => row.relative_path).filter((path): path is string => Boolean(path))
}

function goRoot() {
  query.path = undefined
  query.name = undefined
  query.page_no = 1
  return loadData()
}

function goPath(index: number) {
  query.path = pathParts.value.slice(0, index + 1).join('/')
  query.name = undefined
  query.page_no = 1
  return loadData()
}

function enterDirectory(row: ResourceItem) {
  if (!row.is_dir || !row.relative_path) return
  query.path = row.relative_path
  query.name = undefined
  query.page_no = 1
  return loadData()
}

function formatSize(size: number | null | undefined) {
  if (size === null || size === undefined) return '—'
  if (size === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let value = size
  let unitIndex = 0
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex += 1
  }
  return `${value.toFixed(value >= 10 || unitIndex === 0 ? 0 : 2)} ${units[unitIndex]}`
}

function formatDateTime(value?: string) {
  return value ? value.replace('T', ' ').slice(0, 19) : '—'
}

function openFilePicker() {
  fileInput.value?.click()
}

async function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  if (query.path) formData.append('target_path', query.path)
  uploading.value = true
  try {
    await ResourceAPI.uploadFile(formData)
    ElMessage.success('文件上传成功')
    await loadData()
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function handleDownload(row: ResourceItem) {
  if (!row.is_file || !row.relative_path) return
  const response = await ResourceAPI.downloadFile(row.relative_path)
  download.saveAs(response.data, row.name)
}

async function handleExport() {
  exporting.value = true
  try {
    const response = await ResourceAPI.exportResource({ name: query.name, path: query.path })
    download.saveAs(response.data, `resource-${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('资源列表导出成功')
  } finally {
    exporting.value = false
  }
}

async function handleDelete(targetRows: ResourceItem[]) {
  const paths = targetRows.map((row) => row.relative_path).filter((path): path is string => Boolean(path))
  if (!paths.length) return
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${paths.length} 个资源吗？目录删除后将递归删除其中内容。`, '删除资源', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })
    await ResourceAPI.deleteResource(paths)
    ElMessage.success('资源已删除')
    await loadData()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    throw error
  }
}

async function handleBatchDelete() {
  const targets = rows.value.filter((row) => row.relative_path && selectedPaths.value.includes(row.relative_path))
  await handleDelete(targets)
}

function openCreateDirectory() {
  Object.assign(createDirectoryForm, { parent_path: query.path || '', dir_name: '' })
  createDirectoryVisible.value = true
  createDirectoryFormRef.value?.clearValidate()
}

async function handleCreateDirectory() {
  const valid = await createDirectoryFormRef.value?.validate().catch(() => false)
  if (valid === false) return
  submitting.value = true
  try {
    await ResourceAPI.createDirectory({ ...createDirectoryForm })
    ElMessage.success('目录创建成功')
    createDirectoryVisible.value = false
    await loadData()
  } finally {
    submitting.value = false
  }
}

function openRename(row: ResourceItem) {
  if (!row.relative_path) return
  operationType.value = 'rename'
  Object.assign(operationForm, { old_path: row.relative_path, new_name: row.name, source_path: '', target_path: '', overwrite: false })
  operationVisible.value = true
}

function openTransfer(row: ResourceItem, type: 'move' | 'copy') {
  if (!row.relative_path) return
  operationType.value = type
  Object.assign(operationForm, { old_path: '', new_name: '', source_path: row.relative_path, target_path: '', overwrite: false })
  operationVisible.value = true
}

async function handleOperation() {
  submitting.value = true
  try {
    if (operationType.value === 'rename') {
      const payload: ResourceRenameQuery = { old_path: operationForm.old_path, new_name: operationForm.new_name.trim() }
      if (!payload.new_name) {
        ElMessage.warning('请输入新的名称')
        return
      }
      await ResourceAPI.renameResource(payload)
    } else {
      const targetPath = operationForm.target_path.trim()
      if (!targetPath) {
        ElMessage.warning('请输入目标路径')
        return
      }
      const payload: ResourceMoveQuery = { source_path: operationForm.source_path, target_path: targetPath, overwrite: operationForm.overwrite }
      if (operationType.value === 'move') await ResourceAPI.moveResource(payload)
      else await ResourceAPI.copyResource(payload)
    }
    ElMessage.success(operationType.value === 'rename' ? '资源已重命名' : operationType.value === 'move' ? '资源已移动' : '资源已复制')
    operationVisible.value = false
    await loadData()
  } finally {
    submitting.value = false
  }
}

onMounted(loadData)
</script>

<style scoped lang="scss">
.monitor-page { min-height: 100%; padding: 14px 4px 36px; color: var(--app-text); }
.page-heading, .card-heading, .heading-actions, .card-heading-actions, .pagination-row, .path-bar, .resource-name, .name-link { display: flex; align-items: center; }
.page-heading { justify-content: space-between; gap: 24px; padding: 6px 0 24px; border-bottom: 1px solid var(--app-border); }
.eyebrow, .section-index { margin: 0; color: var(--el-color-primary); font-size: 11px; font-weight: 700; letter-spacing: .12em; }
h1 { margin: 8px 0 0; font-size: clamp(28px, 4vw, 46px); letter-spacing: -.045em; line-height: 1; }
.heading-copy, .card-note, .summary-label, .summary-card small { color: var(--app-muted); }
.heading-copy { margin: 12px 0 0; font-size: 13px; }
.heading-actions { flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
.summary-row { margin: 16px 0 0; }
.summary-card { min-height: 112px; }
.summary-label, .summary-card small { display: block; }
.summary-label { font-size: 12px; }
.summary-card strong { display: block; margin: 8px 0 4px; color: var(--el-color-primary); font-size: 30px; line-height: 1; font-variant-numeric: tabular-nums; }
.summary-card small { font-size: 11px; }
.content-card { margin-top: 16px; }
.card-heading { justify-content: space-between; gap: 16px; }
.card-heading > div { display: flex; align-items: center; gap: 10px; }
.card-heading-actions { gap: 12px; }
.path-bar { flex-wrap: wrap; gap: 2px; min-height: 34px; margin-bottom: 8px; padding: 4px 10px; background: var(--app-surface-muted); border: 1px solid var(--app-border); }
.path-label { margin-right: 6px; color: var(--app-muted); font-size: 12px; }
.path-separator { color: var(--app-muted); }
.search-bar { display: flex; flex-wrap: wrap; gap: 0 12px; margin-bottom: 4px; }
.data-table { width: 100%; }
.resource-name, .name-link { gap: 8px; }
.resource-name .el-icon, .name-link .el-icon { color: var(--el-color-primary); }
.name-link { padding: 0; color: var(--el-color-primary); font: inherit; text-align: left; background: transparent; border: 0; cursor: pointer; }
.name-link:hover { text-decoration: underline; }
.danger-text { color: var(--el-color-danger); }
code, .path-value { color: var(--el-color-primary); font-family: var(--app-mono); font-size: 12px; }
.path-value { overflow-wrap: anywhere; }
.pagination-row { justify-content: flex-end; padding-top: 16px; }
.hidden-input { display: none; }
@media (max-width: 760px) {
  .page-heading { align-items: flex-start; flex-direction: column; }
  .heading-actions { justify-content: flex-start; }
  .card-heading, .card-heading-actions { align-items: flex-start; flex-direction: column; }
  .card-heading-actions { gap: 4px; }
}
</style>
