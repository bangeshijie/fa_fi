<template>
  <section class="admin-page">
    <header class="page-heading">
      <div>
        <div class="heading-title-row">
          <h2>预算明细</h2>
          <p class="eyebrow">BUDGET / BUDGET DETAIL</p>
        </div>
        <p class="heading-copy">维护预算版本、公司、科目、成本中心和归属月份之间的预算明细关系。</p>
      </div>
      <div class="heading-actions">
        <el-tag type="info" effect="plain">预算数据</el-tag>
        <el-button :loading="loading" @click="loadData"><el-icon>
            <Refresh />
          </el-icon>刷新</el-button>
        <el-button v-permission="'module_budget:budget_detail:download'" plain @click="handleDownloadTemplate"><el-icon>
            <Download />
          </el-icon>模板</el-button>
        <el-button v-permission="'module_budget:budget_detail:import'" plain @click="openImport"><el-icon>
            <Upload />
          </el-icon>批量导入</el-button>
        <el-button v-permission="'module_budget:budget_detail:export'" type="primary" plain :loading="exporting"
          @click="handleExport"><el-icon>
            <Download />
          </el-icon>导出</el-button>
        <el-button v-permission="'module_budget:budget_detail:create'" type="primary" @click="openCreate"><el-icon>
            <Plus />
          </el-icon>新增预算</el-button>
      </div>
    </header>

    <el-card shadow="never" class="content-card">
      <template #header>
        <div class="card-heading">
          <div><span class="section-index">01</span><strong>预算明细清单</strong></div><el-button
            v-permission="'module_budget:budget_detail:delete'" text type="danger" :disabled="!selectedIds.length"
            @click="handleBatchDelete"><el-icon>
              <Delete />
            </el-icon>删除所选</el-button>
        </div>
      </template>
      <el-form :inline="true" class="search-bar" @submit.prevent="handleSearch">
        <el-form-item label="预算版本"><el-select v-model="query.budget_version" clearable filterable placeholder="全部预算版本"
            class="select-field"><el-option v-for="option in budgetVersionOptions" :key="option.dict_value"
              :value="option.dict_value"
              :label="`${option.dict_value} ${option.dict_label || ''}`" /></el-select></el-form-item>
        <el-form-item label="年度"><el-input-number v-model="query.year" :min="1900" :max="2999" controls-position="right"
            class="short-field" /></el-form-item>
        <el-form-item label="月份"><el-select v-model="query.belonging_months" multiple collapse-tags
            collapse-tags-tooltip clearable placeholder="全部月份" class="month-field"><el-option
              v-for="month in monthOptions" :key="month" :value="month" :label="`${month}月`" /></el-select></el-form-item>
        <el-form-item label="公司"><el-select v-model="query.company_id" clearable filterable placeholder="全部公司"
            class="select-field"><el-option v-for="item in companyOptions" :key="item.id" :value="item.id"
              :label="`${item.code} · ${item.name}`" /></el-select></el-form-item>
        <el-form-item label="部门"><el-cascader v-model="query.department_ids" :options="departmentOptions"
            :props="departmentCascaderProps" clearable filterable collapse-tags collapse-tags-tooltip
            placeholder="全部部门，选择上级包含下级" class="wide-field" /></el-form-item>
        <el-form-item label="会计科目"><el-select v-model="query.accounting_subject_ids" multiple collapse-tags
            collapse-tags-tooltip clearable filterable placeholder="全部会计科目" class="wide-field"><el-option
              v-for="item in subjectOptions" :key="item.id" :value="item.id"
              :label="`${item.code} · ${item.name}`" /></el-select></el-form-item>
        <el-form-item label="成本中心"><el-select v-model="query.cost_center_ids" multiple collapse-tags
            collapse-tags-tooltip clearable filterable placeholder="全部成本中心" class="wide-field"><el-option
              v-for="item in costCenterOptions" :key="item.id" :value="item.id"
              :label="`${item.code} · ${item.name}`" /></el-select></el-form-item>

        <el-form-item label="来源"><el-select v-model="query.data_source_category" multiple collapse-tags
            collapse-tags-tooltip clearable placeholder="全部来源" class="source-field"><el-option value="原始"
              label="原始" /><el-option value="调整" label="调整" /></el-select></el-form-item>
        <el-form-item class="search-actions"><el-button type="primary" @click="handleSearch"><el-icon>
              <Search />
            </el-icon>查询</el-button><el-button @click="handleReset">重置</el-button></el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="rows" border stripe row-key="id" class="data-table"
        @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="48" fixed="left" /><el-table-column prop="budget_version" label="预算版本"
          min-width="150" fixed="left"><template #default="{ row }"><code>{{ row.budget_version }}</code><span
              class="secondary-text">{{ getDictLabel(budgetVersionOptions, row.budget_version)
              }}</span></template></el-table-column><el-table-column prop="year" label="年度" width="76" align="center" />
        <el-table-column label="公司" min-width="150" show-overflow-tooltip><template
            #default="{ row }"><code>{{ row.company_code }}</code><span class="secondary-text">{{ row.company_name
              }}</span></template></el-table-column>
        <el-table-column label="会计科目" min-width="180" show-overflow-tooltip><template
            #default="{ row }"><code>{{ row.accounting_subject_code }}</code><span class="secondary-text">{{
              row.accounting_subject_name }}</span></template></el-table-column>
        <el-table-column label="成本中心" min-width="150" show-overflow-tooltip><template #default="{ row }"><template
              v-if="row.cost_center_code"><code>{{ row.cost_center_code }}</code><span class="secondary-text">{{
                row.cost_center_name }}</span></template><span v-else
              class="muted">未设置</span></template></el-table-column>
        <el-table-column prop="belonging_month" label="归属月" width="82" align="center"><template #default="{ row }">{{
          row.belonging_month }}月</template></el-table-column><el-table-column prop="currency" label="币种" width="78"
          align="center" /><el-table-column prop="amount" label="金额" width="132" align="right"><template
            #default="{ row }">{{ formatAmount(row.amount) }}</template></el-table-column><el-table-column
          prop="budget_text" label="预算文本" min-width="160" show-overflow-tooltip /><el-table-column
          prop="data_source_category" label="数据来源分类" width="112"><template #default="{ row }"><el-tag
              :type="row.data_source_category === '原始' ? 'info' : 'warning'" effect="plain">{{ row.data_source_category
              }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="172" fixed="right" align="center"><template #default="{ row }"><el-button
              v-permission="'module_budget:budget_detail:detail'" link type="primary" @click="openDetail(row)"><el-icon>
                <View />
              </el-icon>详情</el-button><el-button v-permission="'module_budget:budget_detail:update'" link type="primary"
              @click="openEdit(row)">编辑</el-button><el-button v-permission="'module_budget:budget_detail:delete'" link
              type="danger" @click="handleDelete(row)">删除</el-button></template></el-table-column>
      </el-table>
      <el-empty v-if="!loading && !rows.length" description="暂无预算明细，请先新增或批量导入记录" />
      <div class="pagination-row"><span class="amount-summary">金额汇总：{{ formatAmount(amountSum) }}</span><el-pagination
          v-model:current-page="query.page_no" v-model:page-size="query.page_size" :total="total"
          :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next, jumper" @change="loadData" /></div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="860px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="126px" class="edit-form"><el-row
          :gutter="18">
          <el-col :xs="24" :sm="12"><el-form-item label="预算版本" prop="budget_version"><el-select
                v-model="form.budget_version" :disabled="isDetail" filterable placeholder="请选择预算版本"
                class="full-field"><el-option v-for="option in budgetVersionOptions" :key="option.dict_value"
                  :value="option.dict_value"
                  :label="`${option.dict_value} ${option.dict_label || ''}`" /></el-select></el-form-item></el-col>
          <el-col :xs="24" :sm="12"><el-form-item label="年度" prop="year"><el-input-number v-model="form.year"
                :disabled="isDetail" :min="1900" :max="2999" controls-position="right"
                class="full-field" /></el-form-item></el-col>
          <el-col :xs="24" :sm="12"><el-form-item label="公司" prop="company_id"><el-select v-model="form.company_id"
                :disabled="isDetail" filterable class="full-field" placeholder="请选择公司"><el-option
                  v-for="item in companyOptions" :key="item.id" :value="item.id"
                  :label="`${item.code} · ${item.name}`" /></el-select></el-form-item></el-col><el-col :xs="24"
            :sm="12"><el-form-item label="会计科目" prop="accounting_subject_id"><el-select
                v-model="form.accounting_subject_id" :disabled="isDetail" filterable class="full-field"
                placeholder="请选择会计科目"><el-option v-for="item in subjectOptions" :key="item.id" :value="item.id"
                  :label="`${item.code} · ${item.name}`" /></el-select></el-form-item></el-col>
          <el-col :xs="24" :sm="12"><el-form-item label="成本中心" prop="cost_center_id"><el-select
                v-model="form.cost_center_id" :disabled="isDetail" filterable clearable class="full-field"
                placeholder="可不选"><el-option v-for="item in costCenterOptions" :key="item.id" :value="item.id"
                  :label="`${item.code} · ${item.name}`" /></el-select></el-form-item></el-col><el-col :xs="24"
            :sm="12"><el-form-item label="归属月份" prop="belonging_month"><el-input-number v-model="form.belonging_month"
                :disabled="isDetail" :min="1" :max="12" controls-position="right"
                class="full-field" /></el-form-item></el-col>
          <el-col :xs="24" :sm="8"><el-form-item label="币种" prop="currency"><el-input v-model="form.currency"
                :disabled="isDetail" maxlength="16" placeholder="默认 RMB" /></el-form-item></el-col><el-col :xs="24"
            :sm="8"><el-form-item label="金额" prop="amount"><el-input-number v-model="form.amount" :disabled="isDetail"
                :precision="2" :step="0.01" controls-position="right"
                class="full-field" /></el-form-item></el-col><el-col :xs="24" :sm="8"><el-form-item label="数据来源分类"
              prop="data_source_category"><el-radio-group v-model="form.data_source_category"
                :disabled="isDetail"><el-radio value="原始">原始</el-radio><el-radio
                  value="调整">调整</el-radio></el-radio-group></el-form-item></el-col>
          <el-col :xs="24" :sm="12"><el-form-item label="预算文本" prop="budget_text"><el-input v-model="form.budget_text"
                :disabled="isDetail" maxlength="500" /></el-form-item></el-col><el-col :xs="24" :sm="12"><el-form-item
              label="数据来源说明" prop="source_description"><el-input v-model="form.source_description" :disabled="isDetail"
                maxlength="2000" /></el-form-item></el-col>
        </el-row></el-form>
      <template #footer><el-button @click="dialogVisible = false">{{ isDetail ? '关闭' : '取消' }}</el-button><el-button
          v-if="!isDetail" type="primary" :loading="submitting" @click="handleSubmit">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="importDialogVisible" title="批量导入预算明细" width="560px" destroy-on-close>
      <el-alert title="请先下载模板并保留表头；预算版本请使用启用的字典项。每行数据都会新增一条预算明细。" type="info" :closable="false" show-icon />
      <div class="import-container">
        <el-button link type="primary" @click="handleDownloadTemplate">下载导入模板</el-button>
        <el-upload ref="uploadRef" :auto-upload="false" :limit="1" accept=".xlsx,.xls" :show-file-list="true"
          :on-change="handleFileChange" :on-remove="handleFileRemove">
          <el-button>选择 Excel 文件</el-button>
          <template #tip>
            <div class="el-upload__tip">仅支持 .xlsx / .xls；币种和金额必填，数据来源分类可填写“原始”或“调整”。</div>
          </template>
        </el-upload>
      </div>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="importLoading" :disabled="!importFile"
          @click="handleImport">开始导入</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importResultVisible" title="预算明细导入结果" width="820px" destroy-on-close>
      <template v-if="importResult">
        <el-alert :title="importResult.failed_count ? '导入已完成，但有部分数据未成功处理。' : '全部数据已成功处理。'"
          :type="importResult.failed_count ? 'warning' : 'success'" show-icon :closable="false" />
        <div class="import-result-summary">
          <div class="import-result-item"><span>数据总数</span><strong>{{ importResult.total_count }}</strong></div>
          <div class="import-result-item import-result-item--success"><span>成功处理</span><strong>{{
            importResult.success_count }}</strong></div>
          <div class="import-result-item import-result-item--primary"><span>新增</span><strong>{{
            importResult.created_count }}</strong></div>
          <div class="import-result-item import-result-item--danger"><span>失败</span><strong>{{ importResult.failed_count
              }}</strong></div>
        </div>
        <el-table v-if="importResult.errors.length" :data="importResult.errors" border stripe max-height="360px">
          <el-table-column prop="row_number" label="Excel行号" width="100" />
          <el-table-column prop="budget_version" label="预算版本" min-width="180" />
          <el-table-column prop="reason" label="失败原因" min-width="360" show-overflow-tooltip />
        </el-table>
        <p v-if="importResult.errors_truncated" class="result-note">失败明细仅展示前 200 条。</p>
      </template>
      <template #footer><el-button type="primary" @click="handleImportResultConfirm">完成</el-button></template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Delete, Download, Plus, Refresh, Search, Upload, View } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules, type UploadFile, type UploadInstance } from 'element-plus'
import AccountingSubjectAPI, { type AccountingSubjectOption } from '@/api/module_dimension/accounting_subject'
import CompanyAPI from '@/api/module_dimension/company'
import CostCenterAPI, { type CostCenterOption, type CompanyOption } from '@/api/module_dimension/cost_center'
import DeptAPI, { type DeptTable } from '@/api/module_system/dept'
import BudgetDetailAPI, { type BudgetDetailForm, type BudgetDetailImportResult, type BudgetDetailPageQuery, type BudgetDetailTable } from '@/api/module_budget/budget_detail'
import { useDictOptions } from '@/hooks'
import { BUDGET_VERSION_DICT_TYPE, getDictLabel } from '@/utils/dict'
import download from '@/utils/download'
import { isHttpError } from '@/utils/request'
import { getPreviousMonthPeriod } from '@/utils'

defineOptions({ name: 'BudgetDetail' })
const loading = ref(false); const exporting = ref(false); const submitting = ref(false); const rows = ref<BudgetDetailTable[]>([]); const total = ref(0); const amountSum = ref<number | string>(0); const selectedIds = ref<number[]>([]); const dialogVisible = ref(false); const dialogMode = ref<'create' | 'edit' | 'detail'>('create'); const editingId = ref<number>(); const formRef = ref<FormInstance>()
const importDialogVisible = ref(false); const importResultVisible = ref(false); const importLoading = ref(false); const importFile = ref<File | null>(null); const importResult = ref<BudgetDetailImportResult | null>(null); const uploadRef = ref<UploadInstance>()
const companyOptions = ref<CompanyOption[]>([]); const subjectOptions = ref<AccountingSubjectOption[]>([]); const costCenterOptions = ref<CostCenterOption[]>([]); const departmentOptions = ref<DeptTable[]>([])
const departmentCascaderProps = { value: 'id', label: 'name', children: 'children', multiple: true, checkStrictly: true, emitPath: false }
const monthOptions = Array.from({ length: 12 }, (_, index) => index + 1)
const defaultPeriod = getPreviousMonthPeriod()
const query = reactive<BudgetDetailPageQuery>({ page_no: 1, page_size: 10, year: defaultPeriod.year, belonging_months: [defaultPeriod.month], accounting_subject_ids: [], cost_center_ids: [], department_ids: [] }); const form = reactive<BudgetDetailForm>({ year: new Date().getFullYear(), belonging_month: new Date().getMonth() + 1, currency: 'RMB', data_source_category: '原始' })
const { options: budgetVersionOptions, load: loadBudgetVersionOptions } = useDictOptions(BUDGET_VERSION_DICT_TYPE)
const formRules: FormRules<BudgetDetailForm> = { budget_version: [{ required: true, message: '请选择预算版本', trigger: 'change' }], year: [{ required: true, message: '请输入年度', trigger: 'change' }], company_id: [{ required: true, message: '请选择公司', trigger: 'change' }], accounting_subject_id: [{ required: true, message: '请选择会计科目', trigger: 'change' }], belonging_month: [{ required: true, message: '请输入归属月份', trigger: 'change' }], currency: [{ required: true, message: '请输入币种', trigger: 'blur' }], amount: [{ required: true, message: '请输入金额', trigger: 'change' }], data_source_category: [{ required: true, message: '请选择数据来源分类', trigger: 'change' }] }
const dialogTitle = computed(() => ({ create: '新增预算明细', edit: '编辑预算明细', detail: '预算明细详情' })[dialogMode.value]); const isDetail = computed(() => dialogMode.value === 'detail'); const formatAmount = (value: number | string | null | undefined) => { const amount = Number(value ?? 0); return Number.isFinite(amount) ? amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00' }
async function loadData() { loading.value = true; try { const response = await BudgetDetailAPI.list({ ...query }); const result = response.data.data; rows.value = result?.items || []; total.value = result?.total || 0; amountSum.value = result?.amount_sum ?? 0; selectedIds.value = [] } finally { loading.value = false } }
async function loadOptions() { const [departments, companies, subjects, costCenters] = await Promise.all([DeptAPI.listDept(), CompanyAPI.listCompanyOptions(), AccountingSubjectAPI.options(), CostCenterAPI.listOptions()]); await loadBudgetVersionOptions(); departmentOptions.value = departments.data.data || []; companyOptions.value = companies.data.data || []; subjectOptions.value = subjects.data.data || []; costCenterOptions.value = costCenters.data.data || [] }
function handleSearch() { query.page_no = 1; return loadData() }
function handleReset() { const previousPeriod = getPreviousMonthPeriod(); query.budget_version = undefined; query.year = previousPeriod.year; query.company_id = undefined; query.accounting_subject_ids = []; query.cost_center_ids = []; query.department_ids = []; query.belonging_months = [previousPeriod.month]; query.data_source_category = undefined; query.page_no = 1; return loadData() }
function handleSelectionChange(selection: BudgetDetailTable[]) { selectedIds.value = selection.map((row) => row.id) }
function resetForm() { Object.assign(form, { budget_version: undefined, year: new Date().getFullYear(), company_id: undefined, accounting_subject_id: undefined, cost_center_id: null, belonging_month: new Date().getMonth() + 1, currency: 'RMB', amount: undefined, budget_text: undefined, data_source_category: '原始', source_description: undefined }); editingId.value = undefined; formRef.value?.clearValidate() }
function openCreate() { resetForm(); dialogMode.value = 'create'; dialogVisible.value = true }
function openEdit(row: BudgetDetailTable) { resetForm(); Object.assign(form, row); editingId.value = row.id; dialogMode.value = 'edit'; dialogVisible.value = true }
async function openDetail(row: BudgetDetailTable) { const response = await BudgetDetailAPI.detail(row.id); resetForm(); Object.assign(form, response.data.data); dialogMode.value = 'detail'; dialogVisible.value = true }
async function handleSubmit() { const valid = await formRef.value?.validate().catch(() => false); if (valid === false) return; submitting.value = true; try { if (dialogMode.value === 'edit' && editingId.value) { await BudgetDetailAPI.update(editingId.value, form); ElMessage.success('预算明细更新成功') } else { await BudgetDetailAPI.create(form); ElMessage.success('预算明细创建成功') }; dialogVisible.value = false; await loadData() } finally { submitting.value = false } }
async function handleDelete(row: BudgetDetailTable) { try { await ElMessageBox.confirm(`确定删除预算版本“${row.budget_version}”吗？`, '删除预算明细', { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }); await BudgetDetailAPI.delete([row.id]); ElMessage.success('预算明细已删除'); await loadData() } catch (error) { if (error === 'cancel' || error === 'close') return; throw error } }
async function handleBatchDelete() { try { await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 条预算明细吗？`, '批量删除预算明细', { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }); await BudgetDetailAPI.delete(selectedIds.value); ElMessage.success('选中预算明细已删除'); await loadData() } catch (error) { if (error === 'cancel' || error === 'close') return; throw error } }
async function handleExport() { exporting.value = true; try { const { page_no: _pageNo, page_size: _pageSize, ...filters } = query; const response = await BudgetDetailAPI.export(filters); const day = new Date().toLocaleDateString('en-CA'); download.saveAs(response.data, `budget-detail-${day}.xlsx`); ElMessage.success('预算明细导出成功') } finally { exporting.value = false } }
async function handleDownloadTemplate() { const response = await BudgetDetailAPI.downloadTemplate(); download.saveAs(response.data, '预算明细导入模板.xlsx'); ElMessage.success('模板下载成功') }
function openImport() { importFile.value = null; importDialogVisible.value = true }
function handleFileChange(uploadFile: UploadFile) { importFile.value = uploadFile.raw || null }
function handleFileRemove() { importFile.value = null }
async function handleImport() {
  if (!importFile.value) { ElMessage.warning('请选择 Excel 文件'); return }
  importLoading.value = true
  try {
    const response = await BudgetDetailAPI.importData(importFile.value)
    importResult.value = response.data.data || null; importResultVisible.value = true; importDialogVisible.value = false
    ElMessage.success(response.data.data?.failed_count ? '导入完成，但有失败数据' : '导入成功')
    uploadRef.value?.clearFiles(); importFile.value = null
  } catch (error) {
    if (isHttpError(error)) {
      const result = (error.data as ApiResponse<BudgetDetailImportResult> | undefined)?.data
      if (result) { importResult.value = result; importResultVisible.value = true; importDialogVisible.value = false; uploadRef.value?.clearFiles(); importFile.value = null; return }
    }
    throw error
  } finally { importLoading.value = false }
}
async function handleImportResultConfirm() { importResultVisible.value = false; await loadData() }
onMounted(async () => { await Promise.all([loadData(), loadOptions()]) })
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
.muted,
.secondary-text {
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
  width: 190px;
}

.wide-field {
  width: 260px;
}

.source-field {
  width: 220px;
}

.short-field {
  width: 110px;
}

.month-field {
  width: 170px;
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

.secondary-text {
  display: block;
  margin-top: 3px;
  font-size: 12px;
}

.pagination-row {
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding-top: 16px;
}

.amount-summary {
  color: var(--app-muted);
  font-size: 13px;
  font-weight: 700;
}

.edit-form {
  padding: 8px 12px 0;
}

.full-field {
  width: 100%;
}

.import-container {
  display: grid;
  gap: 16px;
  margin-top: 18px;
}

.import-result-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin: 18px 0;
}

.import-result-item {
  padding: 12px 8px;
  border: 1px solid var(--app-border);
  text-align: center;
}

.import-result-item span {
  display: block;
  color: var(--app-muted);
  font-size: 12px;
}

.import-result-item strong {
  display: block;
  margin-top: 6px;
  color: var(--app-text);
  font-size: 22px;
}

.import-result-item--success strong {
  color: var(--el-color-success);
}

.import-result-item--primary strong {
  color: var(--el-color-primary);
}

.import-result-item--warning strong {
  color: var(--el-color-warning);
}

.import-result-item--danger strong {
  color: var(--el-color-danger);
}

.result-note {
  color: var(--app-muted);
  font-size: 12px;
}

@media (max-width: 760px) {
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .heading-actions {
    justify-content: flex-start;
  }
}
</style>
