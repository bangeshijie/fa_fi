<template>
  <section class="admin-page">
    <header class="page-heading">
      <div>
        <div class="heading-title-row">
          <h2>参数管理</h2>
          <p class="eyebrow">SYSTEM / PARAMETER</p>
        </div>
        <p class="heading-copy">维护系统运行参数。参数键名创建后不可修改，参数值会同步到缓存。</p>
      </div>
      <div class="heading-actions">
        <el-tag type="info" effect="plain">系统配置</el-tag>
        <el-button :loading="loading" @click="loadData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button v-permission="'module_system:param:export'" type="primary" plain :loading="exporting"
          @click="handleExport">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
        <el-button v-permission="'module_system:param:create'" type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>
          新增参数
        </el-button>
      </div>
    </header>

    <el-row :gutter="12" class="summary-row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">参数总数</span>
          <strong>{{ total }}</strong>
          <small>符合当前筛选</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">内置参数</span>
          <strong>{{ builtInCount }}</strong>
          <small>当前页系统内置</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">正常状态</span>
          <strong>{{ enabledCount }}</strong>
          <small>当前页正常参数</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">已选记录</span>
          <strong>{{ selectedIds.length }}</strong>
          <small>可批量删除</small>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="content-card">
      <template #header>
        <div class="card-heading">
          <div><span class="section-index">01</span><strong>参数列表</strong></div>
          <el-button v-permission="'module_system:param:delete'" text type="danger" :disabled="!selectedIds.length"
            @click="handleBatchDelete">
            <el-icon><Delete /></el-icon>
            删除所选
          </el-button>
        </div>
      </template>

      <el-form :inline="true" class="search-bar" @submit.prevent="handleSearch">
        <el-form-item label="参数名称">
          <el-input v-model="query.config_name" clearable placeholder="请输入参数名称" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="参数键名">
          <el-input v-model="query.config_key" clearable placeholder="请输入参数键名" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="参数类型">
          <el-select v-model="query.config_type" clearable placeholder="全部类型" class="select-field">
            <el-option :value="true" label="系统内置" />
            <el-option :value="false" label="自定义" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" clearable placeholder="全部状态" class="select-field">
            <el-option value="0" label="正常" />
            <el-option value="1" label="停用" />
          </el-select>
        </el-form-item>
        <el-form-item label="创建时间">
          <el-date-picker v-model="query.created_time" type="datetimerange" value-format="YYYY-MM-DD HH:mm:ss"
            start-placeholder="开始时间" end-placeholder="结束时间" range-separator="至" class="date-field" />
        </el-form-item>
        <el-form-item class="search-actions">
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon>查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="rows" border stripe row-key="id" class="data-table"
        @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="48" fixed="left" />
        <el-table-column type="index" label="#" width="58" align="center" />
        <el-table-column prop="config_name" label="参数名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="config_key" label="参数键名" min-width="220" show-overflow-tooltip>
          <template #default="{ row }"><code>{{ row.config_key }}</code></template>
        </el-table-column>
        <el-table-column label="参数值" min-width="220" show-overflow-tooltip>
          <template #default="{ row }"><span class="value-preview">{{ row.config_value || '—' }}</span></template>
        </el-table-column>
        <el-table-column label="类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="row.config_type ? 'warning' : 'info'" effect="plain" size="small">
              {{ row.config_type ? '系统内置' : '自定义' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === '0' ? 'success' : 'danger'" effect="plain" size="small">
              {{ row.status === '0' ? '正常' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
        <el-table-column prop="created_time" label="创建时间" width="178" show-overflow-tooltip />
        <el-table-column label="操作" width="166" fixed="right" align="center">
          <template #default="{ row }">
            <el-button v-permission="'module_system:param:detail'" link type="primary" @click="openDetail(row)">
              <el-icon><View /></el-icon>详情
            </el-button>
            <el-button v-permission="'module_system:param:update'" link type="primary" @click="openEdit(row)">
              编辑
            </el-button>
            <el-button v-permission="'module_system:param:delete'" link type="danger" @click="handleDelete(row)">
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="620px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="96px" class="edit-form">
        <el-form-item label="参数名称" prop="config_name">
          <el-input v-model="form.config_name" :disabled="isDetail" maxlength="64" show-word-limit />
        </el-form-item>
        <el-form-item label="参数键名" prop="config_key">
          <el-input v-model="form.config_key" :disabled="isDetail || dialogMode === 'edit'" maxlength="500">
            <template #prefix><el-icon><Key /></el-icon></template>
          </el-input>
          <span class="form-tip">小写字母开头，仅支持小写字母、数字、点、横线和下划线。</span>
        </el-form-item>
        <el-form-item label="参数值" prop="config_value">
          <el-input v-model="form.config_value" :disabled="isDetail" type="textarea" :rows="4"
            placeholder="请输入参数值" />
        </el-form-item>
        <el-form-item label="参数类型" prop="config_type">
          <el-switch v-model="form.config_type" :disabled="isDetail" active-text="系统内置" inactive-text="自定义" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status" :disabled="isDetail">
            <el-radio value="0">正常</el-radio>
            <el-radio value="1">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" :disabled="isDetail" type="textarea" :rows="3" maxlength="500"
            show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ isDetail ? '关闭' : '取消' }}</el-button>
        <el-button v-if="!isDetail" type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Delete, Download, Key, Plus, Refresh, Search, View } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'

import ParamsAPI, { type ConfigForm, type ConfigPageQuery, type ConfigTable } from '@/api/module_system/params'
import download from '@/utils/download'

defineOptions({ name: 'Params' })

const loading = ref(false)
const exporting = ref(false)
const submitting = ref(false)
const rows = ref<ConfigTable[]>([])
const total = ref(0)
const selectedIds = ref<number[]>([])
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit' | 'detail'>('create')
const editingId = ref<number>()
const formRef = ref<FormInstance>()
const query = reactive<ConfigPageQuery>({ page_no: 1, page_size: 10 })
const form = reactive<ConfigForm>({ config_type: false, status: '0' })

const formRules: FormRules<ConfigForm> = {
  config_name: [{ required: true, message: '请输入参数名称', trigger: 'blur' }],
  config_key: [
    { required: true, message: '请输入参数键名', trigger: 'blur' },
    { pattern: /^[a-z][a-z0-9_.-]*$/, message: '参数键名格式不正确', trigger: 'blur' },
  ],
}

const dialogTitle = computed(() => ({ create: '新增参数', edit: '编辑参数', detail: '参数详情' })[dialogMode.value])
const isDetail = computed(() => dialogMode.value === 'detail')
const builtInCount = computed(() => rows.value.filter((row) => row.config_type).length)
const enabledCount = computed(() => rows.value.filter((row) => row.status === '0').length)

async function loadData() {
  loading.value = true
  try {
    const response = await ParamsAPI.listParams({ ...query })
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
  query.config_name = undefined
  query.config_key = undefined
  query.config_type = undefined
  query.status = undefined
  query.created_time = undefined
  query.page_no = 1
  return loadData()
}

function handleSelectionChange(selection: ConfigTable[]) {
  selectedIds.value = selection.map((row) => row.id).filter((id): id is number => typeof id === 'number')
}

function resetForm() {
  Object.assign(form, { config_name: undefined, config_key: undefined, config_value: undefined, config_type: false, status: '0', description: undefined })
  editingId.value = undefined
  formRef.value?.clearValidate()
}

function openCreate() {
  resetForm()
  dialogMode.value = 'create'
  dialogVisible.value = true
}

function openEdit(row: ConfigTable) {
  resetForm()
  Object.assign(form, row)
  editingId.value = row.id
  dialogMode.value = 'edit'
  dialogVisible.value = true
}

async function openDetail(row: ConfigTable) {
  if (!row.id) return
  const response = await ParamsAPI.detailParams(row.id)
  resetForm()
  Object.assign(form, response.data.data)
  dialogMode.value = 'detail'
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (valid === false) return
  submitting.value = true
  try {
    if (dialogMode.value === 'edit' && editingId.value) {
      await ParamsAPI.updateParams(editingId.value, { ...form })
      ElMessage.success('参数更新成功')
    } else {
      await ParamsAPI.createParams({ ...form })
      ElMessage.success('参数创建成功')
    }
    dialogVisible.value = false
    await loadData()
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row: ConfigTable) {
  if (!row.id) return
  await ElMessageBox.confirm(`确定删除参数“${row.config_name || row.config_key}”吗？`, '删除参数', {
    type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消',
  })
  await ParamsAPI.deleteParams([row.id])
  ElMessage.success('参数已删除')
  await loadData()
}

async function handleBatchDelete() {
  if (!selectedIds.value.length) return
  await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 条参数吗？`, '批量删除参数', {
    type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消',
  })
  await ParamsAPI.deleteParams(selectedIds.value)
  ElMessage.success('选中参数已删除')
  await loadData()
}

async function handleExport() {
  exporting.value = true
  try {
    const response = await ParamsAPI.exportParams({ ...query })
    download.saveAs(response.data, `system-params-${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('参数导出成功')
  } finally {
    exporting.value = false
  }
}

onMounted(loadData)
</script>

<style scoped lang="scss">
.admin-page { min-height: 100%; padding: 14px 4px 36px; color: var(--app-text); }
.page-heading, .card-heading, .heading-actions, .pagination-row { display: flex; align-items: center; }
.page-heading { justify-content: space-between; gap: 24px; padding: 6px 0 24px; border-bottom: 1px solid var(--app-border); }
.eyebrow, .section-index { margin: 0; color: var(--el-color-primary); font-size: 11px; font-weight: 700; letter-spacing: .12em; }
.heading-copy, .card-heading small, .form-tip { color: var(--app-muted); }
.heading-copy { margin: 12px 0 0; font-size: 13px; }
.heading-actions { flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
.summary-row { margin: 16px 0; }
.summary-card { min-height: 112px; }
.summary-label, .summary-card small { display: block; color: var(--app-muted); }
.summary-label { font-size: 12px; }
.summary-card strong { display: block; margin: 8px 0 4px; color: var(--el-color-primary); font-size: 30px; line-height: 1; }
.summary-card small { font-size: 11px; }
.content-card { margin-top: 16px; }
.card-heading { justify-content: space-between; gap: 16px; }
.card-heading > div { display: flex; align-items: center; gap: 10px; }
.search-bar { display: flex; flex-wrap: wrap; gap: 0 12px; margin-bottom: 4px; }
.select-field { width: 118px; }
.date-field { width: 350px; }
code { color: var(--el-color-primary); font-family: var(--app-mono); font-size: 12px; }
.value-preview { display: block; overflow: hidden; color: var(--app-muted); text-overflow: ellipsis; white-space: nowrap; }
.pagination-row { justify-content: flex-end; padding-top: 16px; }
.edit-form { padding: 8px 12px 0; }
.form-tip { display: block; margin-top: 4px; font-size: 11px; line-height: 1.5; }
@media (max-width: 760px) {
  .page-heading { align-items: flex-start; flex-direction: column; }
  .heading-actions { justify-content: flex-start; }
  .date-field { width: min(350px, 100%); }
}
</style>
