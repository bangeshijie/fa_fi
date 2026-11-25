<template>
  <section class="admin-page">
    <header class="page-heading">
      <div>
        <div class="heading-title-row">
          <h2>会计科目管理</h2>
          <p class="eyebrow">DIMENSION / ACCOUNTING SUBJECT</p>
        </div>
        <p class="heading-copy">维护会计科目代码、报表归属和管理分类。</p>
      </div>
      <div class="heading-actions">
        <el-tag type="info" effect="plain">主数据</el-tag>
        <el-button :loading="loading" @click="loadData">
          <el-icon>
            <Refresh />
          </el-icon>刷新
        </el-button>
        <el-button v-permission="'module_dimension:accounting_subject:download'" plain @click="handleDownloadTemplate">
          <el-icon>
            <Download />
          </el-icon>模板
        </el-button>
        <el-button v-permission="'module_dimension:accounting_subject:import'" plain @click="openImport">
          <el-icon>
            <Upload />
          </el-icon>批量导入
        </el-button>
        <el-button v-permission="'module_dimension:accounting_subject:export'" type="primary" plain :loading="exporting"
          @click="handleExport">
          <el-icon>
            <Download />
          </el-icon>导出
        </el-button>
        <el-button v-permission="'module_dimension:accounting_subject:create'" type="primary" @click="openCreate">
          <el-icon>
            <Plus />
          </el-icon>新增会计科目
        </el-button>
      </div>
    </header>

    <el-row :gutter="12" class="summary-row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">会计科目总数</span>
          <strong>{{ total }}</strong>
          <small>符合当前筛选</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">当前页正常</span>
          <strong>{{ activeCount }}</strong>
          <small>状态为正常</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">当前页停用</span>
          <strong>{{ disabledCount }}</strong>
          <small>状态为停用</small>
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
          <div><span class="section-index">01</span><strong>会计科目清单</strong></div>
          <el-button v-permission="'module_dimension:accounting_subject:delete'" text type="danger"
            :disabled="!selectedIds.length" @click="handleBatchDelete">
            <el-icon>
              <Delete />
            </el-icon>删除所选
          </el-button>
        </div>
      </template>

      <el-form :inline="true" class="search-bar" @submit.prevent="handleSearch">
        <el-form-item label="代码">
          <el-input v-model="query.code" clearable placeholder="请输入会计科目代码" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="query.name" clearable placeholder="请输入会计科目名称" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="余额方向">
          <el-select v-model="query.balance_direction" clearable placeholder="全部方向" class="select-field">
            <el-option value="借" label="借" />
            <el-option value="贷" label="贷" />
          </el-select>
        </el-form-item>
        <el-form-item label="会计报表科目">
          <el-input v-model="query.accounting_statement_subject" clearable placeholder="所属会计报表科目" />
        </el-form-item>
        <el-form-item label="管理分类">
          <el-cascader v-model="selectedCategoryPaths" :options="categoryOptions" :props="categoryCascaderProps"
            clearable filterable collapse-tags collapse-tags-tooltip placeholder="全部管理分类" class="category-field"
            @change="handleCategoryChange" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" clearable placeholder="全部状态" class="select-field">
            <el-option value="0" label="正常" />
            <el-option value="1" label="停用" />
          </el-select>
        </el-form-item>
        <el-form-item class="search-actions">
          <el-button type="primary" @click="handleSearch">
            <el-icon>
              <Search />
            </el-icon>查询
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="rows" border stripe row-key="id" class="data-table"
        @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="48" fixed="left" />
        <el-table-column prop="id" label="ID" width="68" align="center" />
        <el-table-column prop="code" label="会计科目代码" width="154" fixed="left">
          <template #default="{ row }"><code>{{ row.code }}</code></template>
        </el-table-column>
        <el-table-column prop="name" label="会计科目名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="balance_direction" label="余额方向" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="info" effect="plain" size="small">{{ row.balance_direction }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="accounting_statement_subject" label="所属会计报表科目" min-width="180" show-overflow-tooltip />

        <el-table-column prop="management_category_level1" label="管理一级分类" min-width="150" show-overflow-tooltip />
        <el-table-column prop="management_category_level2" label="管理二级分类" min-width="150" show-overflow-tooltip />
        <el-table-column prop="management_category_level3" label="管理三级分类" min-width="180" show-overflow-tooltip />
        <el-table-column label="状态" width="104" align="center">
          <template #default="{ row }">
            <el-switch v-if="hasPermission('module_dimension:accounting_subject:patch')"
              :model-value="row.status === '0'" inline-prompt active-text="正常" inactive-text="停用"
              @change="handleStatusChange(row, $event)" />
            <el-tag v-else :type="row.status === '0' ? 'success' : 'danger'" effect="plain" size="small">
              {{ row.status === '0' ? '正常' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="166" fixed="right" align="center">
          <template #default="{ row }">
            <el-button v-permission="'module_dimension:accounting_subject:detail'" link type="primary"
              @click="openDetail(row)">
              <el-icon>
                <View />
              </el-icon>详情
            </el-button>
            <el-button v-permission="'module_dimension:accounting_subject:update'" link type="primary"
              @click="openEdit(row)">
              编辑
            </el-button>
            <el-button v-permission="'module_dimension:accounting_subject:delete'" link type="danger"
              @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && !rows.length" description="暂无会计科目主数据，请先新增或批量导入" />
      <div class="pagination-row">
        <el-pagination v-model:current-page="query.page_no" v-model:page-size="query.page_size" :total="total"
          :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next, jumper" @change="loadData" />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="860px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="148px" class="edit-form">
        <el-row :gutter="18">
          <el-col :xs="24" :sm="12">
            <el-form-item label="会计科目代码" prop="code">
              <el-input v-model="form.code" :disabled="isDetail" maxlength="32" show-word-limit
                placeholder="请输入唯一科目代码" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="会计科目名称" prop="name">
              <el-input v-model="form.name" :disabled="isDetail" maxlength="128" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="科目余额方向" prop="balance_direction">
              <el-select v-model="form.balance_direction" :disabled="isDetail" placeholder="请选择余额方向" class="full-field">
                <el-option value="借" label="借" />
                <el-option value="贷" label="贷" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="所属会计报表科目" prop="accounting_statement_subject">
              <el-input v-model="form.accounting_statement_subject" :disabled="isDetail" maxlength="128" />
            </el-form-item>
          </el-col>

          <el-col :xs="24" :sm="12">
            <el-form-item label="管理科目一级分类" prop="management_category_level1">
              <el-input v-model="form.management_category_level1" :disabled="isDetail" maxlength="64" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="管理科目二级分类" prop="management_category_level2">
              <el-input v-model="form.management_category_level2" :disabled="isDetail" maxlength="64" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="管理三级分类" prop="management_category_level3">
              <el-input v-model="form.management_category_level3" :disabled="isDetail" maxlength="128" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="状态" prop="status">
              <el-radio-group v-model="form.status" :disabled="isDetail">
                <el-radio value="0">正常</el-radio>
                <el-radio value="1">停用</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :xs="24">
            <el-form-item label="备注" prop="description">
              <el-input v-model="form.description" :disabled="isDetail" type="textarea" :rows="3" maxlength="500"
                show-word-limit />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ isDetail ? '关闭' : '取消' }}</el-button>
        <el-button v-if="!isDetail" type="primary" :loading="submitting" @click="handleSubmit">
          保存
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDialogVisible" title="批量导入会计科目" width="560px" destroy-on-close>
      <el-alert title="请先下载模板并保留表头。科目余额方向填写借或贷；相同会计科目代码会更新已有记录。" type="info" :closable="false" show-icon />
      <div class="import-container">
        <el-button link type="primary" @click="handleDownloadTemplate">下载导入模板</el-button>
        <el-upload ref="uploadRef" :auto-upload="false" :limit="1" accept=".xlsx,.xls" :show-file-list="true"
          :on-change="handleFileChange" :on-remove="handleFileRemove">
          <el-button>选择 Excel 文件</el-button>
          <template #tip>
            <div class="el-upload__tip">仅支持 .xlsx / .xls；状态可填写“正常”或“停用”。</div>
          </template>
        </el-upload>
      </div>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="importLoading" :disabled="!importFile" @click="handleImport">
          开始导入
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importResultVisible" title="会计科目导入结果" width="820px" destroy-on-close>
      <template v-if="importResult">
        <el-alert :title="importResult.failed_count
          ? '导入已完成，但有部分数据未成功处理。'
          : '全部数据已成功处理。'
          " :type="importResult.failed_count ? 'warning' : 'success'" show-icon :closable="false" />
        <div class="import-result-summary">
          <div class="import-result-item">
            <span>数据总数</span><strong>{{ importResult.total_count }}</strong>
          </div>
          <div class="import-result-item import-result-item--success">
            <span>成功处理</span><strong>{{ importResult.success_count }}</strong>
          </div>
          <div class="import-result-item import-result-item--primary">
            <span>新增</span><strong>{{ importResult.created_count }}</strong>
          </div>
          <div class="import-result-item import-result-item--warning">
            <span>更新</span><strong>{{ importResult.updated_count }}</strong>
          </div>
          <div class="import-result-item">
            <span>已有代码</span><strong>{{ importResult.duplicate_count }}</strong>
          </div>
          <div class="import-result-item import-result-item--danger">
            <span>失败</span><strong>{{ importResult.failed_count }}</strong>
          </div>
        </div>
        <el-table v-if="importResult.errors.length" :data="importResult.errors" border stripe max-height="360px">
          <el-table-column prop="row_number" label="Excel 行号" width="110" align="center" />
          <el-table-column prop="code" label="会计科目代码" width="180" show-overflow-tooltip />
          <el-table-column prop="reason" label="失败原因" min-width="360" show-overflow-tooltip />
        </el-table>
        <p v-if="importResult.errors_truncated" class="result-note">
          失败明细较多，页面仅展示前 200 条。
        </p>
      </template>
      <template #footer>
        <el-button @click="importResultVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleImportResultConfirm">刷新列表</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Delete, Download, Plus, Refresh, Search, Upload, View } from '@element-plus/icons-vue'
import {
  ElMessage,
  ElMessageBox,
  type FormInstance,
  type FormRules,
  type UploadFile,
  type UploadInstance,
} from 'element-plus'

import AccountingSubjectAPI, {
  type AccountingSubjectForm,
  type AccountingSubjectCategoryOption,
  type AccountingSubjectImportResult,
  type AccountingSubjectPageQuery,
  type AccountingSubjectTable,
} from '@/api/module_dimension/accounting_subject'
import { hasPermission } from '@/directives/permission'
import download from '@/utils/download'
import { isHttpError } from '@/utils/request'

defineOptions({ name: 'AccountingSubjectMasterData' })

const loading = ref(false)
const exporting = ref(false)
const submitting = ref(false)
const importLoading = ref(false)
const rows = ref<AccountingSubjectTable[]>([])
const total = ref(0)
const selectedIds = ref<number[]>([])
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit' | 'detail'>('create')
const editingId = ref<number>()
const formRef = ref<FormInstance>()
const query = reactive<AccountingSubjectPageQuery>({ page_no: 1, page_size: 10 })
const form = reactive<AccountingSubjectForm>({ status: '0' })
const categoryOptions = ref<AccountingSubjectCategoryOption[]>([])
const selectedCategoryPaths = ref<string[][]>([])
const categoryCascaderProps = {
  multiple: true,
  checkStrictly: true,
  emitPath: true,
}
const importDialogVisible = ref(false)
const importResultVisible = ref(false)
const importFile = ref<File | null>(null)
const importResult = ref<AccountingSubjectImportResult | null>(null)
const uploadRef = ref<UploadInstance>()

const formRules: FormRules<AccountingSubjectForm> = {
  code: [
    { required: true, message: '请输入会计科目代码', trigger: 'blur' },
    {
      pattern: /^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$/,
      message: '代码仅支持字母、数字、点、下划线或短横线',
      trigger: 'blur',
    },
  ],
  name: [{ required: true, message: '请输入会计科目名称', trigger: 'blur' }],
  balance_direction: [{ required: true, message: '请选择科目余额方向', trigger: 'change' }],
}

const dialogTitle = computed(
  () =>
    ({
      create: '新增会计科目',
      edit: '编辑会计科目',
      detail: '会计科目详情',
    })[dialogMode.value],
)
const isDetail = computed(() => dialogMode.value === 'detail')
const activeCount = computed(() => rows.value.filter((row) => row.status === '0').length)
const disabledCount = computed(() => rows.value.filter((row) => row.status !== '0').length)

async function loadData() {
  loading.value = true
  try {
    const response = await AccountingSubjectAPI.list({ ...query })
    const result = response.data.data
    rows.value = result?.items || []
    total.value = result?.total || 0
    selectedIds.value = []
  } finally {
    loading.value = false
  }
}

async function loadCategoryOptions() {
  const response = await AccountingSubjectAPI.categoryOptions()
  categoryOptions.value = response.data.data || []
}

function handleCategoryChange(value: unknown) {
  const paths = Array.isArray(value)
    ? value
      .filter((path): path is unknown[] => Array.isArray(path))
      .map((path) => path.map((item) => String(item)))
    : []
  selectedCategoryPaths.value = paths
  query.management_category_paths = paths.length
    ? paths.map((path) => JSON.stringify(path))
    : undefined
}

function handleSearch() {
  query.page_no = 1
  return loadData()
}

function handleReset() {
  query.code = undefined
  query.name = undefined
  query.balance_direction = undefined
  query.accounting_statement_subject = undefined
  selectedCategoryPaths.value = []
  query.management_category_paths = undefined
  query.status = undefined
  query.page_no = 1
  return loadData()
}

function handleSelectionChange(selection: AccountingSubjectTable[]) {
  selectedIds.value = selection.map((row) => row.id)
}

function resetForm() {
  Object.assign(form, {
    code: undefined,
    name: undefined,
    balance_direction: undefined,
    accounting_statement_subject: undefined,
    management_category_level3: undefined,
    management_category_level1: undefined,
    management_category_level2: undefined,
    status: '0',
    description: undefined,
  })
  editingId.value = undefined
  formRef.value?.clearValidate()
}

function openCreate() {
  resetForm()
  dialogMode.value = 'create'
  dialogVisible.value = true
}

function openEdit(row: AccountingSubjectTable) {
  resetForm()
  Object.assign(form, row)
  editingId.value = row.id
  dialogMode.value = 'edit'
  dialogVisible.value = true
}

async function openDetail(row: AccountingSubjectTable) {
  const response = await AccountingSubjectAPI.detail(row.id)
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
    const payload = { ...form, code: form.code?.trim().toUpperCase(), name: form.name?.trim() }
    if (dialogMode.value === 'edit' && editingId.value) {
      await AccountingSubjectAPI.update(editingId.value, payload)
      ElMessage.success('会计科目更新成功')
    } else {
      await AccountingSubjectAPI.create(payload)
      ElMessage.success('会计科目创建成功')
    }
    dialogVisible.value = false
    await loadData()
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row: AccountingSubjectTable) {
  try {
    await ElMessageBox.confirm(`确定删除会计科目“${row.name}”吗？`, '删除会计科目', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
    })
    await AccountingSubjectAPI.delete([row.id])
    ElMessage.success('会计科目已删除')
    await loadData()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    throw error
  }
}

async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedIds.value.length} 个会计科目吗？`,
      '批量删除会计科目',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
      },
    )
    await AccountingSubjectAPI.delete(selectedIds.value)
    ElMessage.success('选中会计科目已删除')
    await loadData()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    throw error
  }
}

async function handleStatusChange(
  row: AccountingSubjectTable,
  value: string | number | boolean,
) {
  try {
    const status = value ? '0' : '1'
    await AccountingSubjectAPI.batchStatus({ ids: [row.id], status })
    row.status = status
    ElMessage.success(status === '0' ? '会计科目已启用' : '会计科目已停用')
  } catch (error) {
    await loadData()
    throw error
  }
}

async function handleExport() {
  exporting.value = true
  try {
    const { page_no: _pageNo, page_size: _pageSize, ...filters } = query
    const response = await AccountingSubjectAPI.export(filters)
    download.saveAs(response.data, `accounting-subjects-${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('会计科目导出成功')
  } finally {
    exporting.value = false
  }
}

async function handleDownloadTemplate() {
  const response = await AccountingSubjectAPI.downloadTemplate()
  download.saveAs(response.data, '会计科目导入模板.xlsx')
  ElMessage.success('模板下载成功')
}

function openImport() {
  importFile.value = null
  importDialogVisible.value = true
}

function handleFileChange(uploadFile: UploadFile) {
  importFile.value = uploadFile.raw || null
}

function handleFileRemove() {
  importFile.value = null
}

async function handleImport() {
  if (!importFile.value) {
    ElMessage.warning('请选择 Excel 文件')
    return
  }
  importLoading.value = true
  try {
    const response = await AccountingSubjectAPI.importData(importFile.value)
    importResult.value = response.data.data || null
    importResultVisible.value = true
    importDialogVisible.value = false
    ElMessage.success(response.data.data?.failed_count ? '导入完成，但有失败数据' : '导入成功')
    uploadRef.value?.clearFiles()
    importFile.value = null
  } catch (error) {
    if (isHttpError(error)) {
      const result = (error.data as ApiResponse<AccountingSubjectImportResult> | undefined)?.data
      if (result) {
        importResult.value = result
        importResultVisible.value = true
        importDialogVisible.value = false
        uploadRef.value?.clearFiles()
        importFile.value = null
        return
      }
    }
    throw error
  } finally {
    importLoading.value = false
  }
}

async function handleImportResultConfirm() {
  importResultVisible.value = false
  await loadData()
}

onMounted(async () => {
  await Promise.all([loadData(), loadCategoryOptions()])
})
</script>

<style scoped lang="scss">
.admin-page {
  min-height: 100%;
  padding: 14px 4px 36px;
  color: var(--app-text);
  font-variant-numeric: tabular-nums;
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
  letter-spacing: 0.12em;
}

.heading-copy,
.result-note {
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
  border-radius: 0;
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
  border-radius: 0;
}

.card-heading {
  justify-content: space-between;
  gap: 16px;
}

.card-heading>div {
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

.select-field {
  width: 170px;
}

.category-field {
  width: 280px;
}

.full-field {
  width: 100%;
}

.data-table {
  --el-table-header-bg-color: #f7f9fc;
  --el-table-border-color: var(--app-border);
}

code {
  color: var(--el-color-primary);
  font-family: var(--app-mono);
  font-size: 12px;
  font-weight: 700;
}

.pagination-row {
  justify-content: flex-end;
  padding-top: 16px;
}

.edit-form {
  padding: 8px 12px 0;
}

.import-container {
  padding: 22px 0 6px;
}

.import-container .el-upload {
  display: block;
  margin-top: 18px;
}

.import-result-summary {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
  margin: 18px 0;
}

.import-result-item {
  padding: 12px;
  border: 1px solid var(--app-border);
  background: #f8fafc;
}

.import-result-item span,
.import-result-item strong {
  display: block;
}

.import-result-item span {
  color: var(--app-muted);
  font-size: 12px;
}

.import-result-item strong {
  margin-top: 6px;
  color: var(--el-color-primary);
  font-size: 24px;
}

.import-result-item--success strong {
  color: var(--el-color-success);
}

.import-result-item--warning strong {
  color: var(--el-color-warning);
}

.import-result-item--danger strong {
  color: var(--el-color-danger);
}

.result-note {
  margin: 10px 0 0;
  font-size: 12px;
}

@media (max-width: 900px) {
  .import-result-summary {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 760px) {
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .heading-actions {
    justify-content: flex-start;
  }

  .import-result-summary {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
