<template>
  <section class="admin-page">
    <header class="page-heading">
      <div>
        <div class="heading-title-row">
          <h2>公司主数据</h2>
          <p class="eyebrow">DIMENSION / COMPANY</p>
        </div>
        <p class="heading-copy">统一维护公司代码、法人信息与控股关系，供后续财务主数据引用。</p>
      </div>
      <div class="heading-actions">
        <el-tag type="info" effect="plain">主数据</el-tag>
        <el-button :loading="loading" @click="loadData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button v-permission="'module_dimension:company:export'" type="primary" plain :loading="exporting"
          @click="handleExport">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
        <el-button v-permission="'module_dimension:company:create'" type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>
          新增公司
        </el-button>
      </div>
    </header>

    <el-row :gutter="12" class="summary-row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">公司总数</span>
          <strong>{{ total }}</strong>
          <small>符合当前筛选</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">正常公司</span>
          <strong>{{ enabledCount }}</strong>
          <small>当前页正常状态</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">存在控股关系</span>
          <strong>{{ holdingCount }}</strong>
          <small>当前页已维护上级公司</small>
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
          <div><span class="section-index">01</span><strong>公司清单</strong></div>
          <el-button v-permission="'module_dimension:company:delete'" text type="danger"
            :disabled="!selectedIds.length" @click="handleBatchDelete">
            <el-icon><Delete /></el-icon>
            删除所选
          </el-button>
        </div>
      </template>

      <el-form :inline="true" class="search-bar" @submit.prevent="handleSearch">
        <el-form-item label="公司代码">
          <el-input v-model="query.code" clearable placeholder="请输入公司代码" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="公司名称">
          <el-input v-model="query.name" clearable placeholder="请输入公司名称" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="query.leader" clearable placeholder="请输入负责人" @keyup.enter="handleSearch" />
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
        <el-table-column prop="id" label="ID" width="74" align="center" />
        <el-table-column prop="code" label="公司代码" width="138" fixed="left">
          <template #default="{ row }"><code>{{ row.code }}</code></template>
        </el-table-column>
        <el-table-column prop="name" label="公司名称" min-width="190" show-overflow-tooltip />
        <el-table-column label="上级控股公司" min-width="190" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.holding_company_code" class="holding-company">
              <el-icon><OfficeBuilding /></el-icon>
              {{ row.holding_company_code }} · {{ row.holding_company_name }}
            </span>
            <span v-else class="muted">未设置</span>
          </template>
        </el-table-column>
        <el-table-column prop="address" label="公司地址" min-width="220" show-overflow-tooltip />
        <el-table-column prop="phone" label="公司电话" width="148" show-overflow-tooltip />
        <el-table-column prop="business_license_no" label="营业执照号码" width="178" show-overflow-tooltip />
        <el-table-column prop="leader" label="公司负责人" width="120" show-overflow-tooltip />
        <el-table-column label="控股比例" width="112" align="right">
          <template #default="{ row }">
            <span v-if="row.holding_ratio !== null && row.holding_ratio !== undefined">{{ row.holding_ratio }}%</span>
            <span v-else class="muted">未设置</span>
          </template>
        </el-table-column>
        <el-table-column label="注册资本" width="148" align="right">
          <template #default="{ row }">
            <span v-if="row.registered_capital !== null && row.registered_capital !== undefined">
              {{ row.registered_capital }} 万元
            </span>
            <span v-else class="muted">未设置</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="104" align="center">
          <template #default="{ row }">
            <el-switch v-permission="'module_dimension:company:patch'" :model-value="row.status === '0'"
              inline-prompt active-text="正常" inactive-text="停用" @change="handleStatusChange(row, $event)" />
            <el-tag v-if="!hasPermission('module_dimension:company:patch')"
              :type="row.status === '0' ? 'success' : 'danger'" effect="plain" size="small">
              {{ row.status === '0' ? '正常' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="176" fixed="right" align="center">
          <template #default="{ row }">
            <el-button v-permission="'module_dimension:company:detail'" link type="primary"
              @click="openDetail(row)">
              <el-icon><View /></el-icon>详情
            </el-button>
            <el-button v-permission="'module_dimension:company:update'" link type="primary" @click="openEdit(row)">
              编辑
            </el-button>
            <el-button v-permission="'module_dimension:company:delete'" link type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && !rows.length" description="暂无公司主数据，请先新增公司" />

      <div class="pagination-row">
        <el-pagination v-model:current-page="query.page_no" v-model:page-size="query.page_size" :total="total"
          :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next, jumper" @change="loadData" />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="760px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="112px" class="edit-form">
        <el-row :gutter="18">
          <el-col :xs="24" :sm="12">
            <el-form-item label="公司代码" prop="code">
              <el-input v-model="form.code" :disabled="isDetail" maxlength="32" show-word-limit placeholder="如：CN001" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="公司名称" prop="name">
              <el-input v-model="form.name" :disabled="isDetail" maxlength="128" show-word-limit />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="上级控股公司" prop="holding_company_id">
              <el-select v-model="form.holding_company_id" :disabled="isDetail" clearable filterable
                placeholder="无上级控股公司" class="full-field">
                <el-option v-for="option in holdingOptions" :key="option.id" :label="`${option.code} · ${option.name}`"
                  :value="option.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="公司负责人" prop="leader">
              <el-input v-model="form.leader" :disabled="isDetail" maxlength="64" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="公司电话" prop="phone">
              <el-input v-model="form.phone" :disabled="isDetail" maxlength="32" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="控股比例(%)" prop="holding_ratio">
              <el-input-number v-model="form.holding_ratio" :disabled="isDetail" :min="0" :max="100"
                :precision="2" :step="0.01" controls-position="right" class="full-field" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="注册资本(万元)" prop="registered_capital">
              <el-input-number v-model="form.registered_capital" :disabled="isDetail" :min="0"
                :precision="2" :step="0.01" controls-position="right" class="full-field" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="营业执照号码" prop="business_license_no">
              <el-input v-model="form.business_license_no" :disabled="isDetail" maxlength="64" />
            </el-form-item>
          </el-col>
          <el-col :xs="24">
            <el-form-item label="公司地址" prop="address">
              <el-input v-model="form.address" :disabled="isDetail" maxlength="255" />
            </el-form-item>
          </el-col>
          <el-col :xs="24">
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
        <el-button v-if="!isDetail" type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Delete, Download, OfficeBuilding, Plus, Refresh, Search, View } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'

import CompanyAPI, {
  type CompanyForm,
  type CompanyOption,
  type CompanyPageQuery,
  type CompanyTable,
} from '@/api/module_dimension/company'
import { hasPermission } from '@/directives/permission'
import download from '@/utils/download'

defineOptions({ name: 'CompanyMasterData' })

const loading = ref(false)
const exporting = ref(false)
const submitting = ref(false)
const rows = ref<CompanyTable[]>([])
const companyOptions = ref<CompanyOption[]>([])
const total = ref(0)
const selectedIds = ref<number[]>([])
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit' | 'detail'>('create')
const editingId = ref<number>()
const formRef = ref<FormInstance>()
const query = reactive<CompanyPageQuery>({ page_no: 1, page_size: 10 })
const form = reactive<CompanyForm>({ status: '0', holding_company_id: null })

const formRules: FormRules<CompanyForm> = {
  code: [
    { required: true, message: '请输入公司代码', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9][A-Za-z0-9_-]{1,31}$/, message: '公司代码格式不正确', trigger: 'blur' },
  ],
  name: [{ required: true, message: '请输入公司名称', trigger: 'blur' }],
}

const dialogTitle = computed(() => ({ create: '新增公司', edit: '编辑公司', detail: '公司详情' })[dialogMode.value])
const isDetail = computed(() => dialogMode.value === 'detail')
const enabledCount = computed(() => rows.value.filter((row) => row.status === '0').length)
const holdingCount = computed(() => rows.value.filter((row) => row.holding_company_id).length)
const holdingOptions = computed(() => companyOptions.value.filter((option) => option.id !== editingId.value))

async function loadData() {
  loading.value = true
  try {
    const response = await CompanyAPI.listCompany({ ...query })
    const result = response.data.data
    rows.value = result?.items || []
    total.value = result?.total || 0
    selectedIds.value = []
  } finally {
    loading.value = false
  }
}

async function loadCompanyOptions() {
  const response = await CompanyAPI.listCompanyOptions()
  companyOptions.value = response.data.data || []
}

function handleSearch() {
  query.page_no = 1
  return loadData()
}

function handleReset() {
  query.code = undefined
  query.name = undefined
  query.leader = undefined
  query.status = undefined
  query.page_no = 1
  return loadData()
}

function handleSelectionChange(selection: CompanyTable[]) {
  selectedIds.value = selection.map((row) => row.id)
}

function resetForm() {
  Object.assign(form, {
    code: undefined,
    name: undefined,
    holding_company_id: null,
    address: undefined,
    phone: undefined,
    business_license_no: undefined,
    leader: undefined,
    holding_ratio: undefined,
    registered_capital: undefined,
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

function openEdit(row: CompanyTable) {
  resetForm()
  Object.assign(form, row)
  editingId.value = row.id
  dialogMode.value = 'edit'
  dialogVisible.value = true
}

async function openDetail(row: CompanyTable) {
  if (!row.id) return
  const response = await CompanyAPI.detailCompany(row.id)
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
      await CompanyAPI.updateCompany(editingId.value, payload)
      ElMessage.success('公司更新成功')
    } else {
      await CompanyAPI.createCompany(payload)
      ElMessage.success('公司创建成功')
    }
    dialogVisible.value = false
    await Promise.all([loadData(), loadCompanyOptions()])
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row: CompanyTable) {
  if (!row.id) return
  try {
    await ElMessageBox.confirm(`确定删除公司“${row.name}”吗？`, '删除公司', {
      type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消',
    })
    await CompanyAPI.deleteCompany([row.id])
    ElMessage.success('公司已删除')
    await Promise.all([loadData(), loadCompanyOptions()])
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    throw error
  }
}

async function handleBatchDelete() {
  if (!selectedIds.value.length) return
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 家公司吗？`, '批量删除公司', {
      type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消',
    })
    await CompanyAPI.deleteCompany(selectedIds.value)
    ElMessage.success('选中公司已删除')
    await Promise.all([loadData(), loadCompanyOptions()])
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    throw error
  }
}

async function handleStatusChange(row: CompanyTable, value: string | number | boolean) {
  try {
    await CompanyAPI.batchCompany({ ids: [row.id], status: value ? '0' : '1' })
    row.status = value ? '0' : '1'
    ElMessage.success(value ? '公司已启用' : '公司已停用')
  } catch (error) {
    await loadData()
    throw error
  }
}

async function handleExport() {
  exporting.value = true
  try {
    const response = await CompanyAPI.exportCompany({ ...query })
    download.saveAs(response.data, `companies-${new Date().toISOString().slice(0, 10)}.xlsx`)
    ElMessage.success('公司主数据导出成功')
  } finally {
    exporting.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadData(), loadCompanyOptions()])
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
  letter-spacing: .12em;
}

.heading-copy,
.muted {
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

.select-field {
  width: 118px;
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

.holding-company {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--app-text);
}

.pagination-row {
  justify-content: flex-end;
  padding-top: 16px;
}

.edit-form {
  padding: 8px 12px 0;
}

@media (max-width: 760px) {
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .heading-actions {
    justify-content: flex-start;
  }

  .pagination-row {
    justify-content: flex-start;
    overflow-x: auto;
  }
}
</style>
