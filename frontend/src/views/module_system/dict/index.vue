<template>
  <section class="admin-page">
    <header class="page-heading">
      <div>
        <div class="heading-title-row">
          <h2>字典管理</h2>
          <p class="eyebrow">SYSTEM / DICTIONARY</p>
        </div>
        <p class="heading-copy">维护业务字典类型和字典数据，统一管理下拉选项与状态标识。</p>
      </div>
      <div class="heading-actions">
        <el-tag type="info" effect="plain">数据字典</el-tag>
        <el-button :loading="loading" @click="loadData">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
        <el-button v-permission="activePanel === 'type' ? 'module_system:dict_type:export' : 'module_system:dict_data:export'"
          type="primary" plain :loading="exporting" @click="handleExport">
          <el-icon><Download /></el-icon>导出
        </el-button>
        <el-button v-permission="activePanel === 'type' ? 'module_system:dict_type:create' : 'module_system:dict_data:create'"
          type="primary" @click="activePanel === 'type' ? openTypeCreate() : openDataCreate()">
          <el-icon><Plus /></el-icon>新增{{ activePanel === 'type' ? '字典类型' : '字典数据' }}
        </el-button>
      </div>
    </header>

    <el-row :gutter="12" class="summary-row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">{{ activePanel === 'type' ? '字典类型' : '字典数据' }}</span>
          <strong>{{ activeTotal }}</strong>
          <small>符合当前筛选</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">正常记录</span>
          <strong>{{ activeEnabledCount }}</strong>
          <small>当前页正常状态</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">停用记录</span>
          <strong>{{ activeRows.length - activeEnabledCount }}</strong>
          <small>当前页停用状态</small>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="summary-card">
          <span class="summary-label">已选记录</span>
          <strong>{{ activeSelectedIds.length }}</strong>
          <small>可批量删除</small>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="content-card">
      <template #header>
        <div class="card-heading">
          <div class="panel-switch">
            <span class="section-index">01</span>
            <el-radio-group v-model="activePanel" size="small">
              <el-radio-button label="type">字典类型</el-radio-button>
              <el-radio-button label="data">字典数据</el-radio-button>
            </el-radio-group>
          </div>
          <el-button v-permission="activePanel === 'type' ? 'module_system:dict_type:delete' : 'module_system:dict_data:delete'"
            text type="danger" :disabled="!activeSelectedIds.length" @click="handleBatchDelete">
            <el-icon><Delete /></el-icon>删除所选
          </el-button>
        </div>
      </template>

      <el-form v-if="activePanel === 'type'" :inline="true" class="search-bar" @submit.prevent="handleSearch">
        <el-form-item label="字典名称">
          <el-input v-model="typeQuery.dict_name" clearable placeholder="请输入字典名称" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="字典类型">
          <el-input v-model="typeQuery.dict_type" clearable placeholder="请输入字典类型" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="typeQuery.status" clearable placeholder="全部状态" class="select-field">
            <el-option value="0" label="正常" /><el-option value="1" label="停用" />
          </el-select>
        </el-form-item>
        <el-form-item label="创建时间">
          <el-date-picker v-model="typeQuery.created_time" type="datetimerange" value-format="YYYY-MM-DD HH:mm:ss"
            start-placeholder="开始时间" end-placeholder="结束时间" range-separator="至" class="date-field" />
        </el-form-item>
        <el-form-item class="search-actions">
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon>查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-form v-else :inline="true" class="search-bar" @submit.prevent="handleSearch">
        <el-form-item label="字典标签">
          <el-input v-model="dataQuery.dict_label" clearable placeholder="请输入字典标签" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="字典类型">
          <el-select v-model="dataQuery.dict_type_id" clearable filterable placeholder="全部类型" class="type-field">
            <el-option v-for="item in typeOptionsWithId" :key="item.id" :value="item.id" :label="item.dict_name || item.dict_type || '未命名'" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="dataQuery.status" clearable placeholder="全部状态" class="select-field">
            <el-option value="0" label="正常" /><el-option value="1" label="停用" />
          </el-select>
        </el-form-item>
        <el-form-item label="创建时间">
          <el-date-picker v-model="dataQuery.created_time" type="datetimerange" value-format="YYYY-MM-DD HH:mm:ss"
            start-placeholder="开始时间" end-placeholder="结束时间" range-separator="至" class="date-field" />
        </el-form-item>
        <el-form-item class="search-actions">
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon>查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-if="activePanel === 'type'" v-loading="loading" :data="typeRows" border stripe row-key="id"
        class="data-table" @selection-change="handleTypeSelection">
        <el-table-column type="selection" width="48" fixed="left" />
        <el-table-column type="index" label="#" width="58" align="center" />
        <el-table-column prop="dict_name" label="字典名称" min-width="180" show-overflow-tooltip />
        <el-table-column label="字典类型" min-width="210" show-overflow-tooltip>
          <template #default="{ row }"><code>{{ row.dict_type }}</code></template>
        </el-table-column>
        <el-table-column label="状态" width="150" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === '0' ? 'success' : 'danger'" effect="plain" size="small">
              {{ row.status === '0' ? '正常' : '停用' }}
            </el-tag>
            <el-button v-permission="'module_system:dict_type:patch'" link size="small"
              :type="row.status === '0' ? 'warning' : 'success'" @click="toggleTypeStatus(row)">
              {{ row.status === '0' ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="190" show-overflow-tooltip />
        <el-table-column prop="created_time" label="创建时间" width="178" show-overflow-tooltip />
        <el-table-column label="操作" width="166" fixed="right" align="center">
          <template #default="{ row }">
            <el-button v-permission="'module_system:dict_type:detail'" link type="primary" @click="openTypeDetail(row)">
              <el-icon><View /></el-icon>详情
            </el-button>
            <el-button v-permission="'module_system:dict_type:update'" link type="primary" @click="openTypeEdit(row)">编辑</el-button>
            <el-button v-permission="'module_system:dict_type:delete'" link type="danger" @click="handleTypeDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-table v-else v-loading="loading" :data="dataRows" border stripe row-key="id" class="data-table"
        @selection-change="handleDataSelection">
        <el-table-column type="selection" width="48" fixed="left" />
        <el-table-column type="index" label="#" width="58" align="center" />
        <el-table-column prop="dict_sort" label="排序" width="80" align="center" />
        <el-table-column prop="dict_label" label="字典标签" min-width="160" show-overflow-tooltip />
        <el-table-column label="字典键值" min-width="170" show-overflow-tooltip>
          <template #default="{ row }"><code>{{ row.dict_value }}</code></template>
        </el-table-column>
        <el-table-column prop="dict_type" label="字典类型" min-width="160" show-overflow-tooltip />
        <el-table-column label="默认" width="80" align="center">
          <template #default="{ row }"><el-tag v-if="row.is_default" type="primary" effect="plain" size="small">默认</el-tag><span v-else class="muted-text">—</span></template>
        </el-table-column>
        <el-table-column label="状态" width="150" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === '0' ? 'success' : 'danger'" effect="plain" size="small">{{ row.status === '0' ? '正常' : '停用' }}</el-tag>
            <el-button v-permission="'module_system:dict_data:patch'" link size="small"
              :type="row.status === '0' ? 'warning' : 'success'" @click="toggleDataStatus(row)">{{ row.status === '0' ? '停用' : '启用' }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="166" fixed="right" align="center">
          <template #default="{ row }">
            <el-button v-permission="'module_system:dict_data:detail'" link type="primary" @click="openDataDetail(row)"><el-icon><View /></el-icon>详情</el-button>
            <el-button v-permission="'module_system:dict_data:update'" link type="primary" @click="openDataEdit(row)">编辑</el-button>
            <el-button v-permission="'module_system:dict_data:delete'" link type="danger" @click="handleDataDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-row">
        <el-pagination v-if="activePanel === 'type'" v-model:current-page="typeQuery.page_no" v-model:page-size="typeQuery.page_size"
          :total="typeTotal" :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next, jumper" @change="loadData" />
        <el-pagination v-else v-model:current-page="dataQuery.page_no" v-model:page-size="dataQuery.page_size"
          :total="dataTotal" :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next, jumper" @change="loadData" />
      </div>
    </el-card>

    <el-dialog v-model="typeDialogVisible" :title="typeDialogTitle" width="560px" destroy-on-close>
      <el-form ref="typeFormRef" :model="typeForm" :rules="typeRules" label-width="92px" class="edit-form">
        <el-form-item label="字典名称" prop="dict_name"><el-input v-model="typeForm.dict_name" :disabled="typeDetail" maxlength="64" /></el-form-item>
        <el-form-item label="字典类型" prop="dict_type"><el-input v-model="typeForm.dict_type" :disabled="typeDetail || typeDialogMode === 'edit'" maxlength="64" /><span class="form-tip">小写字母开头，仅支持小写字母、数字和下划线。</span></el-form-item>
        <el-form-item label="状态" prop="status"><el-radio-group v-model="typeForm.status" :disabled="typeDetail"><el-radio value="0">正常</el-radio><el-radio value="1">停用</el-radio></el-radio-group></el-form-item>
        <el-form-item label="描述" prop="description"><el-input v-model="typeForm.description" :disabled="typeDetail" type="textarea" :rows="3" maxlength="255" show-word-limit /></el-form-item>
      </el-form>
      <template #footer><el-button @click="typeDialogVisible = false">{{ typeDetail ? '关闭' : '取消' }}</el-button><el-button v-if="!typeDetail" type="primary" :loading="submitting" @click="submitType">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="dataDialogVisible" :title="dataDialogTitle" width="640px" destroy-on-close>
      <el-form ref="dataFormRef" :model="dataForm" :rules="dataRules" label-width="92px" class="edit-form">
        <el-form-item label="字典类型" prop="dict_type_id">
          <el-select v-model="dataForm.dict_type_id" :disabled="dataDetail || dataDialogMode === 'edit'" filterable class="full-field" placeholder="请选择字典类型" @change="syncDictType">
            <el-option v-for="item in typeOptionsWithId" :key="item.id" :value="item.id" :label="item.dict_name || item.dict_type || '未命名'" />
          </el-select>
        </el-form-item>
        <el-form-item label="字典标签" prop="dict_label"><el-input v-model="dataForm.dict_label" :disabled="dataDetail" maxlength="100" /></el-form-item>
        <el-form-item label="字典键值" prop="dict_value"><el-input v-model="dataForm.dict_value" :disabled="dataDetail" maxlength="100" /></el-form-item>
        <el-form-item label="排序" prop="dict_sort"><el-input-number v-model="dataForm.dict_sort" :disabled="dataDetail" :min="1" :max="999" /></el-form-item>
        <el-form-item label="默认值" prop="is_default"><el-switch v-model="dataForm.is_default" :disabled="dataDetail" /></el-form-item>
        <el-form-item label="表格样式" prop="list_class"><el-input v-model="dataForm.list_class" :disabled="dataDetail" placeholder="例如 success、warning、danger" maxlength="100" /></el-form-item>
        <el-form-item label="状态" prop="status"><el-radio-group v-model="dataForm.status" :disabled="dataDetail"><el-radio value="0">正常</el-radio><el-radio value="1">停用</el-radio></el-radio-group></el-form-item>
        <el-form-item label="描述" prop="description"><el-input v-model="dataForm.description" :disabled="dataDetail" type="textarea" :rows="3" maxlength="255" show-word-limit /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dataDialogVisible = false">{{ dataDetail ? '关闭' : '取消' }}</el-button><el-button v-if="!dataDetail" type="primary" :loading="submitting" @click="submitData">保存</el-button></template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Delete, Download, Plus, Refresh, Search, View } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'

import DictAPI, { type DictDataForm, type DictDataPageQuery, type DictDataTable, type DictForm, type DictPageQuery, type DictTable } from '@/api/module_system/dict'
import download from '@/utils/download'

defineOptions({ name: 'Dict' })

const activePanel = ref<'type' | 'data'>('type')
const loading = ref(false)
const exporting = ref(false)
const submitting = ref(false)
const typeRows = ref<DictTable[]>([])
const dataRows = ref<DictDataTable[]>([])
const typeTotal = ref(0)
const dataTotal = ref(0)
const typeSelectedIds = ref<number[]>([])
const dataSelectedIds = ref<number[]>([])
const typeOptions = ref<DictTable[]>([])
const typeQuery = reactive<DictPageQuery>({ page_no: 1, page_size: 10 })
const dataQuery = reactive<DictDataPageQuery>({ page_no: 1, page_size: 10 })
const typeForm = reactive<DictForm>({ status: '0' })
const dataForm = reactive<DictDataForm>({ dict_sort: 1, is_default: false, status: '0' })
const typeFormRef = ref<FormInstance>()
const dataFormRef = ref<FormInstance>()
const typeDialogVisible = ref(false)
const dataDialogVisible = ref(false)
const typeDialogMode = ref<'create' | 'edit' | 'detail'>('create')
const dataDialogMode = ref<'create' | 'edit' | 'detail'>('create')
const typeEditingId = ref<number>()
const dataEditingId = ref<number>()

const typeRules: FormRules<DictForm> = {
  dict_name: [{ required: true, message: '请输入字典名称', trigger: 'blur' }],
  dict_type: [{ required: true, message: '请输入字典类型', trigger: 'blur' }, { pattern: /^[a-z][a-z0-9_]*$/, message: '字典类型格式不正确', trigger: 'blur' }],
}
const dataRules: FormRules<DictDataForm> = {
  dict_type_id: [{ required: true, message: '请选择字典类型', trigger: 'change' }],
  dict_label: [{ required: true, message: '请输入字典标签', trigger: 'blur' }],
  dict_value: [{ required: true, message: '请输入字典键值', trigger: 'blur' }],
  dict_sort: [{ required: true, message: '请输入排序', trigger: 'change' }],
}

const activeRows = computed(() => activePanel.value === 'type' ? typeRows.value : dataRows.value)
const typeOptionsWithId = computed(() => typeOptions.value.filter((item): item is DictTable & { id: number } => typeof item.id === 'number'))
const activeTotal = computed(() => activePanel.value === 'type' ? typeTotal.value : dataTotal.value)
const activeSelectedIds = computed(() => activePanel.value === 'type' ? typeSelectedIds.value : dataSelectedIds.value)
const activeEnabledCount = computed(() => activeRows.value.filter((row) => row.status === '0').length)
const typeDialogTitle = computed(() => ({ create: '新增字典类型', edit: '编辑字典类型', detail: '字典类型详情' })[typeDialogMode.value])
const dataDialogTitle = computed(() => ({ create: '新增字典数据', edit: '编辑字典数据', detail: '字典数据详情' })[dataDialogMode.value])
const typeDetail = computed(() => typeDialogMode.value === 'detail')
const dataDetail = computed(() => dataDialogMode.value === 'detail')

async function loadTypeOptions() {
  const response = await DictAPI.optionDictType()
  typeOptions.value = response.data.data || []
}

async function loadData() {
  loading.value = true
  try {
    if (activePanel.value === 'type') {
      const response = await DictAPI.listDictType({ ...typeQuery })
      const result = response.data.data
      typeRows.value = result?.items || []
      typeTotal.value = result?.total || 0
    } else {
      await loadTypeOptions()
      const response = await DictAPI.listDictData({ ...dataQuery })
      const result = response.data.data
      dataRows.value = result?.items || []
      dataTotal.value = result?.total || 0
    }
    if (activePanel.value === 'type') typeSelectedIds.value = []
    else dataSelectedIds.value = []
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  if (activePanel.value === 'type') typeQuery.page_no = 1
  else dataQuery.page_no = 1
  return loadData()
}

function resetSearch() {
  if (activePanel.value === 'type') {
    typeQuery.dict_name = undefined; typeQuery.dict_type = undefined; typeQuery.status = undefined; typeQuery.created_time = undefined; typeQuery.page_no = 1
  } else {
    dataQuery.dict_label = undefined; dataQuery.dict_type_id = undefined; dataQuery.status = undefined; dataQuery.created_time = undefined; dataQuery.page_no = 1
  }
  return loadData()
}

function handleTypeSelection(selection: DictTable[]) { typeSelectedIds.value = selection.map((row) => row.id).filter((id): id is number => typeof id === 'number') }
function handleDataSelection(selection: DictDataTable[]) { dataSelectedIds.value = selection.map((row) => row.id).filter((id): id is number => typeof id === 'number') }

function resetTypeForm() { Object.assign(typeForm, { dict_name: undefined, dict_type: undefined, status: '0', description: undefined }); typeEditingId.value = undefined; typeFormRef.value?.clearValidate() }
function resetDataForm() { Object.assign(dataForm, { dict_sort: 1, dict_label: undefined, dict_value: undefined, dict_type: undefined, dict_type_id: undefined, css_class: undefined, list_class: undefined, is_default: false, status: '0', description: undefined }); dataEditingId.value = undefined; dataFormRef.value?.clearValidate() }

function openTypeCreate() { resetTypeForm(); typeDialogMode.value = 'create'; typeDialogVisible.value = true }
function openTypeEdit(row: DictTable) { resetTypeForm(); Object.assign(typeForm, row); typeEditingId.value = row.id; typeDialogMode.value = 'edit'; typeDialogVisible.value = true }
async function openTypeDetail(row: DictTable) { if (!row.id) return; const response = await DictAPI.detailDictType(row.id); resetTypeForm(); Object.assign(typeForm, response.data.data); typeDialogMode.value = 'detail'; typeDialogVisible.value = true }
async function openDataCreate() { await loadTypeOptions(); resetDataForm(); dataDialogMode.value = 'create'; dataDialogVisible.value = true }
function openDataEdit(row: DictDataTable) { resetDataForm(); Object.assign(dataForm, row); dataEditingId.value = row.id; dataDialogMode.value = 'edit'; dataDialogVisible.value = true }
async function openDataDetail(row: DictDataTable) { if (!row.id) return; const response = await DictAPI.detailDictData(row.id); resetDataForm(); Object.assign(dataForm, response.data.data); dataDialogMode.value = 'detail'; dataDialogVisible.value = true }

function syncDictType(id?: number) {
  const option = typeOptions.value.find((item) => item.id === id)
  dataForm.dict_type = option?.dict_type
}

async function submitType() {
  const valid = await typeFormRef.value?.validate().catch(() => false)
  if (valid === false) return
  submitting.value = true
  try {
    if (typeDialogMode.value === 'edit' && typeEditingId.value) await DictAPI.updateDictType(typeEditingId.value, { ...typeForm })
    else await DictAPI.createDictType({ ...typeForm })
    ElMessage.success('字典类型保存成功'); typeDialogVisible.value = false; await loadData()
  } finally { submitting.value = false }
}

async function submitData() {
  const valid = await dataFormRef.value?.validate().catch(() => false)
  if (valid === false) return
  if (!dataForm.dict_type && dataForm.dict_type_id) syncDictType(dataForm.dict_type_id)
  submitting.value = true
  try {
    if (dataDialogMode.value === 'edit' && dataEditingId.value) await DictAPI.updateDictData(dataEditingId.value, { ...dataForm })
    else await DictAPI.createDictData({ ...dataForm })
    ElMessage.success('字典数据保存成功'); dataDialogVisible.value = false; await loadData()
  } finally { submitting.value = false }
}

async function handleTypeDelete(row: DictTable) { if (!row.id) return; await ElMessageBox.confirm(`确定删除字典类型“${row.dict_name || row.dict_type}”吗？`, '删除字典类型', { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }); await DictAPI.deleteDictType([row.id]); ElMessage.success('字典类型已删除'); await loadData() }
async function handleDataDelete(row: DictDataTable) { if (!row.id) return; await ElMessageBox.confirm(`确定删除字典数据“${row.dict_label || row.dict_value}”吗？`, '删除字典数据', { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }); await DictAPI.deleteDictData([row.id]); ElMessage.success('字典数据已删除'); await loadData() }
async function handleBatchDelete() { const ids = activeSelectedIds.value; if (!ids.length) return; await ElMessageBox.confirm(`确定删除选中的 ${ids.length} 条记录吗？`, '批量删除', { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }); if (activePanel.value === 'type') await DictAPI.deleteDictType(ids); else await DictAPI.deleteDictData(ids); ElMessage.success('选中记录已删除'); await loadData() }

async function toggleTypeStatus(row: DictTable) { if (!row.id) return; await DictAPI.batchDictType({ ids: [row.id], status: row.status === '0' ? '1' : '0' }); ElMessage.success('字典类型状态已更新'); await loadData() }
async function toggleDataStatus(row: DictDataTable) { if (!row.id) return; await DictAPI.batchDictData({ ids: [row.id], status: row.status === '0' ? '1' : '0' }); ElMessage.success('字典数据状态已更新'); await loadData() }

async function handleExport() {
  exporting.value = true
  try {
    if (activePanel.value === 'type') {
      const response = await DictAPI.exportDictType({ ...typeQuery }); download.saveAs(response.data, `dict-type-${new Date().toISOString().slice(0, 10)}.xlsx`)
    } else {
      const response = await DictAPI.exportDictData({ ...dataQuery }); download.saveAs(response.data, `dict-data-${new Date().toISOString().slice(0, 10)}.xlsx`)
    }
    ElMessage.success('字典导出成功')
  } finally { exporting.value = false }
}

watch(activePanel, () => { loadData() })
onMounted(loadData)
</script>

<style scoped lang="scss">
.admin-page { min-height: 100%; padding: 14px 4px 36px; color: var(--app-text); }
.page-heading, .card-heading, .heading-actions, .pagination-row, .panel-switch { display: flex; align-items: center; }
.page-heading { justify-content: space-between; gap: 24px; padding: 6px 0 24px; border-bottom: 1px solid var(--app-border); }
.eyebrow, .section-index { margin: 0; color: var(--el-color-primary); font-size: 11px; font-weight: 700; letter-spacing: .12em; }
.heading-copy, .muted-text, .form-tip { color: var(--app-muted); }
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
.panel-switch { gap: 12px; }
.search-bar { display: flex; flex-wrap: wrap; gap: 0 12px; margin-bottom: 4px; }
.select-field { width: 116px; }
.type-field { width: 170px; }
.date-field { width: 350px; }
.full-field { width: 100%; }
code { color: var(--el-color-primary); font-family: var(--app-mono); font-size: 12px; }
.pagination-row { justify-content: flex-end; padding-top: 16px; }
.edit-form { padding: 8px 12px 0; }
.form-tip { display: block; margin-top: 4px; font-size: 11px; line-height: 1.5; }
@media (max-width: 760px) {
  .page-heading { align-items: flex-start; flex-direction: column; }
  .heading-actions { justify-content: flex-start; }
  .date-field { width: min(350px, 100%); }
  .panel-switch { align-items: flex-start; flex-direction: column; }
}
</style>
