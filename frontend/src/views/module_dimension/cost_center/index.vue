<template>
  <section class="admin-page">
    <header class="page-heading">
      <div>
        <div class="heading-title-row">
          <h2>成本中心管理</h2>
          <p class="eyebrow">DIMENSION / COST CENTER</p>
        </div>
        <p class="heading-copy">维护成本中心代码、公司归属、职能范围和组织负责人信息。</p>
      </div>
      <div class="heading-actions">
        <el-tag type="info" effect="plain">主数据</el-tag>
        <el-button :loading="loading" @click="loadData">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
        <el-button v-permission="'module_dimension:cost_center:download'" plain @click="handleDownloadTemplate">
          <el-icon><Download /></el-icon>模板
        </el-button>
        <el-button v-permission="'module_dimension:cost_center:import'" plain @click="openImport">
          <el-icon><Upload /></el-icon>批量导入
        </el-button>
        <el-button v-permission="'module_dimension:cost_center:export'" type="primary" plain :loading="exporting"
          @click="handleExport">
          <el-icon><Download /></el-icon>导出
        </el-button>
        <el-button v-permission="'module_dimension:cost_center:create'" type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>新增成本中心
        </el-button>
      </div>
    </header>

    <el-row :gutter="12" class="summary-row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">成本中心总数</span>
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
          <div><span class="section-index">01</span><strong>成本中心清单</strong></div>
          <el-button v-permission="'module_dimension:cost_center:delete'" text type="danger"
            :disabled="!selectedIds.length" @click="handleBatchDelete">
            <el-icon><Delete /></el-icon>删除所选
          </el-button>
        </div>
      </template>

      <el-form :inline="true" class="search-bar" @submit.prevent="handleSearch">
        <el-form-item label="代码">
          <el-input v-model="query.code" clearable placeholder="请输入成本中心代码" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="query.name" clearable placeholder="请输入成本中心名称" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="所属公司">
          <el-select v-model="query.company_id" clearable filterable placeholder="全部公司" class="select-field">
            <el-option v-for="option in companyOptions" :key="option.id" :label="`${option.code} · ${option.name}`"
              :value="option.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="职能范围">
          <el-select v-model="query.function_scope" clearable filterable placeholder="全部职能范围" class="select-field">
            <el-option v-for="option in functionScopeOptions" :key="option.dict_value" :value="option.dict_value"
              :label="`${option.dict_value} · ${option.dict_label || ''}`" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" clearable placeholder="全部状态" class="select-field">
            <el-option value="0" label="正常" />
            <el-option value="1" label="停用" />
          </el-select>
        </el-form-item>
        <el-form-item class="search-actions">
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon>查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="rows" border stripe row-key="id" class="data-table"
        @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="48" fixed="left" />
        <el-table-column prop="id" label="ID" width="68" align="center" />
        <el-table-column prop="code" label="成本中心代码" width="150" fixed="left">
          <template #default="{ row }"><code>{{ row.code }}</code></template>
        </el-table-column>
        <el-table-column prop="name" label="成本中心名称" min-width="180" show-overflow-tooltip />
        <el-table-column label="所属公司" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.company_code }} · {{ row.company_name }}</template>
        </el-table-column>
        <el-table-column label="职能范围" width="130" align="center">
          <template #default="{ row }">
            <code>{{ row.function_scope }}</code>
            <span class="scope-label">{{ getDictLabel(functionScopeOptions, row.function_scope) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="所属组织" min-width="170" show-overflow-tooltip>
          <template #default="{ row }">{{ row.dept_code }} · {{ row.dept_name }}</template>
        </el-table-column>
        <el-table-column prop="leader" label="负责人" width="120" show-overflow-tooltip />
        <el-table-column prop="enable_time" label="启用日期" width="130" show-overflow-tooltip />
        <el-table-column label="状态" width="104" align="center">
          <template #default="{ row }">
            <el-switch v-if="hasPermission('module_dimension:cost_center:patch')" :model-value="row.status === '0'"
              inline-prompt active-text="正常" inactive-text="停用" @change="handleStatusChange(row, $event)" />
            <el-tag v-else :type="row.status === '0' ? 'success' : 'danger'" effect="plain" size="small">
              {{ row.status === '0' ? '正常' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="166" fixed="right" align="center">
          <template #default="{ row }">
            <el-button v-permission="'module_dimension:cost_center:detail'" link type="primary" @click="openDetail(row)">
              <el-icon><View /></el-icon>详情
            </el-button>
            <el-button v-permission="'module_dimension:cost_center:update'" link type="primary" @click="openEdit(row)">
              编辑
            </el-button>
            <el-button v-permission="'module_dimension:cost_center:delete'" link type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && !rows.length" description="暂无成本中心主数据，请先新增或批量导入" />
      <div class="pagination-row">
        <el-pagination v-model:current-page="query.page_no" v-model:page-size="query.page_size" :total="total"
          :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next, jumper" @change="loadData" />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="780px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="126px" class="edit-form">
        <el-row :gutter="18">
          <el-col :xs="24" :sm="12">
            <el-form-item label="成本中心代码" prop="code">
              <el-input v-model="form.code" :disabled="isDetail" maxlength="32" show-word-limit placeholder="如：CC400001" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="成本中心名称" prop="name">
              <el-input v-model="form.name" :disabled="isDetail" maxlength="128" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="所属公司" prop="company_id">
              <el-select v-model="form.company_id" :disabled="isDetail" filterable placeholder="请选择公司" class="full-field">
                <el-option v-for="option in companyOptions" :key="option.id" :label="`${option.code} · ${option.name}`"
                  :value="option.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="职能范围" prop="function_scope">
              <el-select v-model="form.function_scope" :disabled="isDetail" filterable placeholder="请选择职能范围" class="full-field">
                <el-option v-for="option in functionScopeOptions" :key="option.dict_value" :value="option.dict_value"
                  :label="`${option.dict_value} · ${option.dict_label || ''}`" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="所属组织" prop="dept_id">
              <el-select v-model="form.dept_id" :disabled="isDetail" filterable placeholder="请选择部门" class="full-field">
                <el-option v-for="option in departmentOptions" :key="option.id" :label="`${option.code} · ${option.name}`"
                  :value="option.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="成本中心负责人" prop="leader">
              <el-input v-model="form.leader" :disabled="isDetail" maxlength="64" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="启用日期" prop="enable_time">
              <el-date-picker v-model="form.enable_time" :disabled="isDetail" type="date"
                value-format="YYYY-MM-DD" placeholder="请选择启用日期" class="full-field" />
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
              <el-input v-model="form.description" :disabled="isDetail" type="textarea" :rows="3" maxlength="500" show-word-limit />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ isDetail ? '关闭' : '取消' }}</el-button>
        <el-button v-if="!isDetail" type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDialogVisible" title="批量导入成本中心" width="540px" destroy-on-close>
      <el-alert title="请先下载模板。所属公司和所属组织请填写代码，职能范围请填写字典代码，启用日期格式为 YYYY-MM-DD。" type="info"
        :closable="false" show-icon />
      <div class="import-container">
        <el-button link type="primary" @click="handleDownloadTemplate">下载导入模板</el-button>
        <el-upload ref="uploadRef" :auto-upload="false" :limit="1" accept=".xlsx,.xls" :show-file-list="true"
          :on-change="handleFileChange" :on-remove="handleFileRemove">
          <el-button>选择 Excel 文件</el-button>
          <template #tip><div class="el-upload__tip">仅支持 .xlsx / .xls 文件；相同成本中心代码会更新已有数据。</div></template>
        </el-upload>
      </div>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="importLoading" :disabled="!importFile" @click="handleImport">开始导入</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importResultVisible" title="成本中心导入结果" width="780px" destroy-on-close>
      <template v-if="importResult">
        <el-alert :title="importResult.failed_count ? '导入已完成，但有部分数据未成功处理。' : '全部数据已成功处理。'"
          :type="importResult.failed_count ? 'warning' : 'success'" show-icon :closable="false" />
        <div class="import-result-summary">
          <div class="import-result-item"><span>数据总数</span><strong>{{ importResult.total_count }}</strong></div>
          <div class="import-result-item import-result-item--success"><span>成功处理</span><strong>{{ importResult.success_count }}</strong></div>
          <div class="import-result-item import-result-item--primary"><span>新增</span><strong>{{ importResult.created_count }}</strong></div>
          <div class="import-result-item import-result-item--warning"><span>更新</span><strong>{{ importResult.updated_count }}</strong></div>
          <div class="import-result-item import-result-item--danger"><span>失败</span><strong>{{ importResult.failed_count }}</strong></div>
        </div>
        <el-table v-if="importResult.errors.length" :data="importResult.errors" border stripe max-height="360px">
          <el-table-column prop="row_number" label="Excel 行号" width="110" align="center" />
          <el-table-column prop="code" label="成本中心代码" width="180" show-overflow-tooltip />
          <el-table-column prop="reason" label="失败原因" min-width="320" show-overflow-tooltip />
        </el-table>
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
import { ElMessage, ElMessageBox, type FormInstance, type FormRules, type UploadFile, type UploadInstance } from 'element-plus'

import CostCenterAPI, {
  type CompanyOption,
  type CostCenterForm,
  type CostCenterImportResult,
  type CostCenterPageQuery,
  type CostCenterTable,
  type DepartmentOption,
} from '@/api/module_dimension/cost_center'
import { hasPermission } from '@/directives/permission'
import { useDictOptions } from '@/hooks'
import { isHttpError } from '@/utils/request'
import download from '@/utils/download'
import { COST_CENTER_FUNCTION_SCOPE_DICT_TYPE, getDictLabel } from '@/utils/dict'

defineOptions({ name: 'CostCenterMasterData' })

function formatLocalDate(value = new Date()) {
  const pad = (number: number) => String(number).padStart(2, '0')
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}`
}

const loading = ref(false)
const exporting = ref(false)
const submitting = ref(false)
const importLoading = ref(false)
const rows = ref<CostCenterTable[]>([])
const companyOptions = ref<CompanyOption[]>([])
const departmentOptions = ref<DepartmentOption[]>([])
const { options: functionScopeOptions, load: loadFunctionScopeOptions } = useDictOptions(
  COST_CENTER_FUNCTION_SCOPE_DICT_TYPE,
)
const total = ref(0)
const selectedIds = ref<number[]>([])
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit' | 'detail'>('create')
const editingId = ref<number>()
const formRef = ref<FormInstance>()
const query = reactive<CostCenterPageQuery>({ page_no: 1, page_size: 10 })
const form = reactive<CostCenterForm>({ status: '0', enable_time: formatLocalDate() })
const importDialogVisible = ref(false)
const importResultVisible = ref(false)
const importFile = ref<File | null>(null)
const importResult = ref<CostCenterImportResult | null>(null)
const uploadRef = ref<UploadInstance>()

const formRules: FormRules<CostCenterForm> = {
  code: [
    { required: true, message: '请输入成本中心代码', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9][A-Za-z0-9_-]{1,31}$/, message: '成本中心代码格式不正确', trigger: 'blur' },
  ],
  name: [{ required: true, message: '请输入成本中心名称', trigger: 'blur' }],
  company_id: [{ required: true, message: '请选择所属公司', trigger: 'change' }],
  function_scope: [
    { required: true, message: '请输入职能范围', trigger: 'blur' },
    { pattern: /^\d{4}$/, message: '职能范围必须为4位数字', trigger: 'blur' },
  ],
  dept_id: [{ required: true, message: '请选择所属组织', trigger: 'change' }],
  enable_time: [{ required: true, message: '请选择启用日期', trigger: 'change' }],
}

const dialogTitle = computed(() => ({ create: '新增成本中心', edit: '编辑成本中心', detail: '成本中心详情' })[dialogMode.value])
const isDetail = computed(() => dialogMode.value === 'detail')
const activeCount = computed(() => rows.value.filter((row) => row.status === '0').length)
const disabledCount = computed(() => rows.value.filter((row) => row.status !== '0').length)

async function loadData() {
  loading.value = true
  try {
    const response = await CostCenterAPI.list({ ...query })
    const result = response.data.data
    rows.value = result?.items || []
    total.value = result?.total || 0
    selectedIds.value = []
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  const [companyResponse, departmentResponse] = await Promise.all([
    CostCenterAPI.listCompanyOptions(),
    CostCenterAPI.listDepartmentOptions(),
  ])
  await loadFunctionScopeOptions()
  companyOptions.value = companyResponse.data.data || []
  departmentOptions.value = departmentResponse.data.data || []
}

function handleSearch() {
  query.page_no = 1
  return loadData()
}

function handleReset() {
  query.code = undefined
  query.name = undefined
  query.company_id = undefined
  query.function_scope = undefined
  query.dept_id = undefined
  query.leader = undefined
  query.status = undefined
  query.page_no = 1
  return loadData()
}

function handleSelectionChange(selection: CostCenterTable[]) {
  selectedIds.value = selection.map((row) => row.id)
}

function resetForm() {
  Object.assign(form, {
    code: undefined,
    name: undefined,
    company_id: undefined,
    function_scope: undefined,
    dept_id: undefined,
    leader: undefined,
    enable_time: formatLocalDate(),
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

function openEdit(row: CostCenterTable) {
  resetForm()
  Object.assign(form, row)
  editingId.value = row.id
  dialogMode.value = 'edit'
  dialogVisible.value = true
}

async function openDetail(row: CostCenterTable) {
  const response = await CostCenterAPI.detail(row.id)
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
    const payload = { ...form, code: form.code?.trim().toUpperCase(), function_scope: form.function_scope?.trim() }
    if (dialogMode.value === 'edit' && editingId.value) {
      await CostCenterAPI.update(editingId.value, payload)
      ElMessage.success('成本中心更新成功')
    } else {
      await CostCenterAPI.create(payload)
      ElMessage.success('成本中心创建成功')
    }
    dialogVisible.value = false
    await loadData()
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row: CostCenterTable) {
  try {
    await ElMessageBox.confirm(`确定删除成本中心“${row.name}”吗？`, '删除成本中心', {
      type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消',
    })
    await CostCenterAPI.delete([row.id])
    ElMessage.success('成本中心已删除')
    await loadData()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    throw error
  }
}

async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 个成本中心吗？`, '批量删除成本中心', {
      type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消',
    })
    await CostCenterAPI.delete(selectedIds.value)
    ElMessage.success('选中成本中心已删除')
    await loadData()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    throw error
  }
}

async function handleStatusChange(row: CostCenterTable, value: string | number | boolean) {
  try {
    const status = value ? '0' : '1'
    await CostCenterAPI.batchStatus({ ids: [row.id], status })
    row.status = status
    ElMessage.success(status === '0' ? '成本中心已启用' : '成本中心已停用')
  } catch (error) {
    await loadData()
    throw error
  }
}

async function handleExport() {
  exporting.value = true
  try {
    const response = await CostCenterAPI.export({ ...query })
    download.saveAs(response.data, `cost-centers-${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('成本中心导出成功')
  } finally {
    exporting.value = false
  }
}

async function handleDownloadTemplate() {
  const response = await CostCenterAPI.downloadTemplate()
  download.saveAs(response.data, '成本中心导入模板.xlsx')
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
    const response = await CostCenterAPI.importData(importFile.value)
    importResult.value = response.data.data || null
    importResultVisible.value = true
    importDialogVisible.value = false
    ElMessage.success(response.data.data?.failed_count ? '导入完成，但有失败数据' : '导入成功')
    uploadRef.value?.clearFiles()
    importFile.value = null
  } catch (error) {
    if (isHttpError(error)) {
      const result = (error.data as ApiResponse<CostCenterImportResult> | undefined)?.data
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
  await Promise.all([loadData(), loadOptions()])
})
</script>

<style scoped lang="scss">
.admin-page { min-height: 100%; padding: 14px 4px 36px; color: var(--app-text); font-variant-numeric: tabular-nums; }
.page-heading, .card-heading, .heading-actions, .pagination-row { display: flex; align-items: center; }
.page-heading { justify-content: space-between; gap: 24px; padding: 6px 0 24px; border-bottom: 1px solid var(--app-border); }
.eyebrow, .section-index { margin: 0; color: var(--el-color-primary); font-size: 11px; font-weight: 700; letter-spacing: .12em; }
.heading-copy, .muted { color: var(--app-muted); }
.heading-copy { margin: 12px 0 0; font-size: 13px; }
.heading-actions { flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
.summary-row { margin: 16px 0; }
.summary-card { min-height: 112px; border-radius: 0; }
.summary-label, .summary-card small { display: block; color: var(--app-muted); }
.summary-label { font-size: 12px; }
.summary-card strong { display: block; margin: 8px 0 4px; color: var(--el-color-primary); font-size: 30px; line-height: 1; }
.summary-card small { font-size: 11px; }
.content-card { margin-top: 16px; border-radius: 0; }
.card-heading { justify-content: space-between; gap: 16px; }
.card-heading > div { display: flex; align-items: center; gap: 10px; }
.search-bar { display: flex; flex-wrap: wrap; gap: 0 12px; margin-bottom: 4px; }
.select-field { width: 170px; }
.full-field { width: 100%; }
.data-table { --el-table-header-bg-color: #f7f9fc; --el-table-border-color: var(--app-border); }
code { color: var(--el-color-primary); font-family: var(--app-mono); font-size: 12px; font-weight: 700; }
.scope-label { display: block; color: var(--app-muted); font-size: 11px; line-height: 1.25; }
.pagination-row { justify-content: flex-end; padding-top: 16px; }
.edit-form { padding: 8px 12px 0; }
.import-container { padding: 22px 0 6px; }
.import-container .el-upload { display: block; margin-top: 18px; }
.import-result-summary { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin: 18px 0; }
.import-result-item { padding: 12px; border: 1px solid var(--app-border); background: #f8fafc; }
.import-result-item span, .import-result-item strong { display: block; }
.import-result-item span { color: var(--app-muted); font-size: 12px; }
.import-result-item strong { margin-top: 6px; color: var(--el-color-primary); font-size: 24px; }
.import-result-item--success strong { color: var(--el-color-success); }
.import-result-item--warning strong { color: var(--el-color-warning); }
.import-result-item--danger strong { color: var(--el-color-danger); }
@media (max-width: 760px) {
  .page-heading { align-items: flex-start; flex-direction: column; }
  .heading-actions { justify-content: flex-start; }
  .pagination-row { justify-content: flex-start; overflow-x: auto; }
  .import-result-summary { grid-template-columns: repeat(2, 1fr); }
}
</style>
