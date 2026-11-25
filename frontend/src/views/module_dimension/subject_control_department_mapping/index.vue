<template>
  <section class="admin-page">
    <header class="page-heading">
      <div>
        <div class="heading-title-row">
          <h2>科目主控部门映射</h2>
          <p class="eyebrow">DIMENSION / SUBJECT CONTROL MAPPING</p>
        </div>
        <p class="heading-copy">维护会计科目和事业部对应的主控部门、主控人。</p>
      </div>
      <div class="heading-actions">
        <el-tag type="info" effect="plain">主数据</el-tag>
        <el-button :loading="loading" @click="loadData"><el-icon><Refresh /></el-icon>刷新</el-button>
        <el-button v-permission="'module_dimension:subject_control_department_mapping:create'" type="primary"
          @click="openCreate"><el-icon><Plus /></el-icon>新增映射</el-button>
      </div>
    </header>

    <el-row :gutter="12" class="summary-row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card"><span class="summary-label">映射总数</span><strong>{{ total }}</strong><small>符合当前筛选</small></el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card"><span class="summary-label">当前页正常</span><strong>{{ activeCount }}</strong><small>状态为正常</small></el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card"><span class="summary-label">当前页停用</span><strong>{{ disabledCount }}</strong><small>状态为停用</small></el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card"><span class="summary-label">已选记录</span><strong>{{ selectedIds.length }}</strong><small>可批量删除</small></el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="content-card">
      <template #header>
        <div class="card-heading">
          <div><span class="section-index">01</span><strong>映射清单</strong></div>
          <el-button v-permission="'module_dimension:subject_control_department_mapping:delete'" text type="danger"
            :disabled="!selectedIds.length" @click="handleBatchDelete"><el-icon><Delete /></el-icon>删除所选</el-button>
        </div>
      </template>

      <el-form :inline="true" class="search-bar" @submit.prevent="handleSearch">
        <el-form-item label="会计科目">
          <el-select v-model="query.accounting_subject_id" clearable filterable placeholder="全部会计科目" class="select-field">
            <el-option v-for="item in options.accounting_subjects" :key="item.id" :value="item.id" :label="`${item.code} · ${item.name}`" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属事业部">
          <el-select v-model="query.dept_id" clearable filterable placeholder="全部事业部" class="select-field">
            <el-option v-for="item in options.departments" :key="item.id" :value="item.id" :label="`${item.code} · ${item.name}`" />
          </el-select>
        </el-form-item>
        <el-form-item label="主控部门">
          <el-input v-model="query.control_department" clearable placeholder="请输入主控部门" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="主控人">
          <el-input v-model="query.control_person" clearable placeholder="请输入主控人" @keyup.enter="handleSearch" />
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

      <el-table v-loading="loading" :data="rows" border stripe row-key="id" class="data-table" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="48" fixed="left" />
        <el-table-column prop="id" label="ID" width="68" align="center" />
        <el-table-column label="会计科目" min-width="220" fixed="left" show-overflow-tooltip>
          <template #default="{ row }"><code>{{ row.accounting_subject_code }}</code><span class="muted-text"> · {{ row.accounting_subject_name }}</span></template>
        </el-table-column>
        <el-table-column label="所属事业部" min-width="190" show-overflow-tooltip>
          <template #default="{ row }"><code>{{ row.dept_code }}</code><span class="muted-text"> · {{ row.dept_name }}</span></template>
        </el-table-column>
        <el-table-column prop="control_department" label="主控部门" min-width="160" show-overflow-tooltip />
        <el-table-column prop="control_person" label="主控人" width="130" show-overflow-tooltip />
        <el-table-column label="状态" width="104" align="center">
          <template #default="{ row }">
            <el-switch v-if="hasPermission('module_dimension:subject_control_department_mapping:patch')" :model-value="row.status === '0'"
              inline-prompt active-text="正常" inactive-text="停用" @change="handleStatusChange(row, $event)" />
            <el-tag v-else :type="row.status === '0' ? 'success' : 'danger'" effect="plain" size="small">{{ row.status === '0' ? '正常' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="166" fixed="right" align="center">
          <template #default="{ row }">
            <el-button v-permission="'module_dimension:subject_control_department_mapping:detail'" link type="primary" @click="openDetail(row)"><el-icon><View /></el-icon>详情</el-button>
            <el-button v-permission="'module_dimension:subject_control_department_mapping:update'" link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button v-permission="'module_dimension:subject_control_department_mapping:delete'" link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && !rows.length" description="暂无科目主控部门映射，请先新增" />
      <div class="pagination-row">
        <el-pagination v-model:current-page="query.page_no" v-model:page-size="query.page_size" :total="total"
          :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next, jumper" @change="loadData" />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="720px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="126px" class="edit-form">
        <el-row :gutter="18">
          <el-col :xs="24" :sm="12">
            <el-form-item label="会计科目" prop="accounting_subject_id">
              <el-select v-model="form.accounting_subject_id" :disabled="isDetail" filterable placeholder="请选择会计科目" class="full-field">
                <el-option v-for="item in options.accounting_subjects" :key="item.id" :value="item.id" :label="`${item.code} · ${item.name}`" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="所属事业部" prop="dept_id">
              <el-select v-model="form.dept_id" :disabled="isDetail" filterable placeholder="请选择事业部" class="full-field">
                <el-option v-for="item in options.departments" :key="item.id" :value="item.id" :label="`${item.code} · ${item.name}`" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="主控部门" prop="control_department"><el-input v-model="form.control_department" :disabled="isDetail" maxlength="128" /></el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="主控人" prop="control_person"><el-input v-model="form.control_person" :disabled="isDetail" maxlength="64" /></el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="状态" prop="status"><el-radio-group v-model="form.status" :disabled="isDetail"><el-radio value="0">正常</el-radio><el-radio value="1">停用</el-radio></el-radio-group></el-form-item>
          </el-col>
          <el-col :xs="24"><el-form-item label="备注" prop="description"><el-input v-model="form.description" :disabled="isDetail" type="textarea" :rows="3" maxlength="500" show-word-limit /></el-form-item></el-col>
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
import { Delete, Plus, Refresh, Search, View } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'

import SubjectControlDepartmentMappingAPI, {
  type SubjectControlDepartmentMappingForm,
  type SubjectControlDepartmentMappingOptions,
  type SubjectControlDepartmentMappingPageQuery,
  type SubjectControlDepartmentMappingTable,
} from '@/api/module_dimension/subject_control_department_mapping'
import { hasPermission } from '@/directives/permission'

defineOptions({ name: 'SubjectControlDepartmentMappingMasterData' })

const loading = ref(false)
const submitting = ref(false)
const rows = ref<SubjectControlDepartmentMappingTable[]>([])
const total = ref(0)
const selectedIds = ref<number[]>([])
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit' | 'detail'>('create')
const editingId = ref<number>()
const formRef = ref<FormInstance>()
const options = ref<SubjectControlDepartmentMappingOptions>({ accounting_subjects: [], departments: [] })
const query = reactive<SubjectControlDepartmentMappingPageQuery>({ page_no: 1, page_size: 10 })
const form = reactive<SubjectControlDepartmentMappingForm>({ status: '0' })

const formRules: FormRules<SubjectControlDepartmentMappingForm> = {
  accounting_subject_id: [{ required: true, message: '请选择会计科目', trigger: 'change' }],
  dept_id: [{ required: true, message: '请选择所属事业部', trigger: 'change' }],
  control_department: [{ required: true, message: '请输入主控部门', trigger: 'blur' }],
  control_person: [{ required: true, message: '请输入主控人', trigger: 'blur' }],
}

const dialogTitle = computed(() => ({ create: '新增科目主控部门映射', edit: '编辑科目主控部门映射', detail: '科目主控部门映射详情' })[dialogMode.value])
const isDetail = computed(() => dialogMode.value === 'detail')
const activeCount = computed(() => rows.value.filter((row) => row.status === '0').length)
const disabledCount = computed(() => rows.value.filter((row) => row.status !== '0').length)

async function loadData() {
  loading.value = true
  try {
    const response = await SubjectControlDepartmentMappingAPI.list({ ...query })
    const result = response.data.data
    rows.value = result?.items || []
    total.value = result?.total || 0
    selectedIds.value = []
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  const response = await SubjectControlDepartmentMappingAPI.options()
  options.value = response.data.data || { accounting_subjects: [], departments: [] }
}

function handleSearch() {
  query.page_no = 1
  return loadData()
}

function handleReset() {
  query.accounting_subject_id = undefined
  query.dept_id = undefined
  query.control_department = undefined
  query.control_person = undefined
  query.status = undefined
  query.page_no = 1
  return loadData()
}

function handleSelectionChange(selection: SubjectControlDepartmentMappingTable[]) {
  selectedIds.value = selection.map((row) => row.id)
}

function resetForm() {
  Object.assign(form, {
    accounting_subject_id: undefined,
    dept_id: undefined,
    control_department: undefined,
    control_person: undefined,
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

function openEdit(row: SubjectControlDepartmentMappingTable) {
  resetForm()
  Object.assign(form, row)
  editingId.value = row.id
  dialogMode.value = 'edit'
  dialogVisible.value = true
}

async function openDetail(row: SubjectControlDepartmentMappingTable) {
  const response = await SubjectControlDepartmentMappingAPI.detail(row.id)
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
    const payload = {
      ...form,
      control_department: form.control_department?.trim(),
      control_person: form.control_person?.trim(),
    }
    if (dialogMode.value === 'edit' && editingId.value) {
      await SubjectControlDepartmentMappingAPI.update(editingId.value, payload)
      ElMessage.success('科目主控部门映射更新成功')
    } else {
      await SubjectControlDepartmentMappingAPI.create(payload)
      ElMessage.success('科目主控部门映射创建成功')
    }
    dialogVisible.value = false
    await loadData()
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row: SubjectControlDepartmentMappingTable) {
  try {
    await ElMessageBox.confirm(`确定删除“${row.accounting_subject_code} · ${row.dept_code}”这条映射吗？`, '删除映射', { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' })
    await SubjectControlDepartmentMappingAPI.delete([row.id])
    ElMessage.success('映射已删除')
    await loadData()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    throw error
  }
}

async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 条映射吗？`, '批量删除映射', { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' })
    await SubjectControlDepartmentMappingAPI.delete(selectedIds.value)
    ElMessage.success('选中映射已删除')
    await loadData()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    throw error
  }
}

async function handleStatusChange(row: SubjectControlDepartmentMappingTable, value: string | number | boolean) {
  try {
    const status = value ? '0' : '1'
    await SubjectControlDepartmentMappingAPI.batchStatus({ ids: [row.id], status })
    row.status = status
    ElMessage.success(status === '0' ? '映射已启用' : '映射已停用')
  } catch (error) {
    await loadData()
    throw error
  }
}

onMounted(async () => {
  await Promise.all([loadData(), loadOptions()])
})
</script>

<style scoped lang="scss">
.admin-page { min-height: 100%; padding: 14px 4px 36px; color: var(--app-text); font-variant-numeric: tabular-nums; }
.page-heading, .card-heading, .heading-actions, .pagination-row { display: flex; align-items: center; }
.page-heading { justify-content: space-between; gap: 24px; padding: 6px 0 24px; border-bottom: 1px solid var(--app-border); }
.heading-title-row { display: flex; align-items: baseline; gap: 14px; }.heading-title-row h2 { margin: 0; font-size: 28px; letter-spacing: -.04em; }.eyebrow, .section-index { margin: 0; color: var(--el-color-primary); font-size: 11px; font-weight: 700; letter-spacing: .12em; }.heading-copy { margin: 12px 0 0; color: var(--app-muted); font-size: 13px; }
.heading-actions { flex-wrap: wrap; justify-content: flex-end; gap: 8px; }.summary-row { margin: 16px 0; }.summary-card { min-height: 112px; border-radius: 0; }.summary-label, .summary-card small { display: block; color: var(--app-muted); }.summary-label { font-size: 12px; }.summary-card strong { display: block; margin: 8px 0 4px; color: var(--el-color-primary); font-size: 30px; line-height: 1; }.summary-card small { font-size: 11px; }.content-card { margin-top: 16px; border-radius: 0; }.card-heading { justify-content: space-between; gap: 16px; }.card-heading > div { display: flex; align-items: center; gap: 10px; }.search-bar { display: flex; flex-wrap: wrap; gap: 0 12px; margin-bottom: 4px; }.select-field { width: 210px; }.data-table { --el-table-header-bg-color: #f7f9fc; --el-table-border-color: var(--app-border); }.muted-text { color: var(--app-muted); }.pagination-row { justify-content: flex-end; padding-top: 16px; }.edit-form { padding: 8px 12px 0; }.full-field { width: 100%; }
@media (max-width: 760px) { .page-heading { align-items: flex-start; flex-direction: column; }.heading-actions { justify-content: flex-start; }.heading-title-row { align-items: flex-start; flex-direction: column; gap: 6px; } }
</style>
