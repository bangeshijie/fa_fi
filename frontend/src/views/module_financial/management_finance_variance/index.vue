<template>
  <section class="analysis-page">
    <header class="page-heading">
      <div>
        <div class="heading-title-row">
          <h2>管财差异分析</h2>
          <p class="eyebrow">FINANCIAL / MANAGEMENT VS FINANCIAL</p>
        </div>
        <p class="heading-copy">按管理分类和会计科目对照管报、财报实际金额，差额为管报减财报。</p>
      </div>
      <div class="heading-actions">
        <el-button :loading="loading" @click="loadAnalysis">
          <el-icon>
            <Refresh />
          </el-icon>刷新
        </el-button>
      </div>
    </header>

    <el-card shadow="never" class="filter-card">
      <template #header>
        <div class="card-heading">
          <div><span class="section-index">01</span><strong>分析口径</strong></div>
          <div class="card-note unit-note">
            <span>金额单位</span>
            <el-radio-group v-model="amountUnit" class="unit-switch">
              <el-radio-button label="wan">万元</el-radio-button>
              <el-radio-button label="yuan">元</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>

      <el-form class="filter-grid" label-position="top" @submit.prevent="handleSearch">
        <el-form-item label="年度" required>
          <el-select v-model="query.year" class="filter-control">
            <el-option v-for="year in yearOptions" :key="year" :value="year" :label="`${year} 年`" />
          </el-select>
        </el-form-item>

        <el-form-item label="截至月份" required>
          <el-select v-model="query.month" class="filter-control">
            <el-option v-for="month in monthOptions" :key="month" :value="month" :label="`${month} 月`" />
          </el-select>
        </el-form-item>

        <el-form-item label="公司">
          <el-select v-model="query.company_ids" multiple collapse-tags collapse-tags-tooltip clearable filterable
            class="filter-control" placeholder="全部公司">
            <el-option v-for="company in companyOptions" :key="company.id" :value="company.id"
              :label="`${company.code} ${company.name}`" />
          </el-select>
        </el-form-item>

        <el-form-item label="部门">
          <el-cascader v-model="query.department_ids" :options="departmentOptions" :props="departmentCascaderProps"
            clearable filterable collapse-tags collapse-tags-tooltip class="filter-control"
            placeholder="全部部门，选择上级包含下级" />
        </el-form-item>

        <el-form-item label="职能范围">
          <el-select v-model="query.function_scopes" multiple collapse-tags collapse-tags-tooltip clearable filterable
            class="filter-control" placeholder="全部职能范围">
            <el-option v-for="option in functionScopeOptions" :key="option.dict_value" :value="option.dict_value"
              :label="`${option.dict_value} ${option.dict_label || ''}`" />
          </el-select>
        </el-form-item>

        <el-form-item label="管理分类">
          <el-cascader v-model="query.management_category_paths" :options="categoryOptions"
            :props="categoryCascaderProps" clearable filterable collapse-tags collapse-tags-tooltip
            class="filter-control" placeholder="全部管理分类" />
        </el-form-item>

        <el-form-item label="管报数据来源">
          <el-select v-model="query.management_data_source_categories" multiple collapse-tags collapse-tags-tooltip
            clearable class="filter-control" placeholder="全部来源">
            <el-option v-for="source in dataSourceOptions" :key="source.value" :value="source.value"
              :label="source.label" />
          </el-select>
        </el-form-item>

        <el-form-item label="财报数据来源">
          <el-select v-model="query.financial_data_source_categories" multiple collapse-tags collapse-tags-tooltip
            clearable class="filter-control" placeholder="全部来源">
            <el-option v-for="source in dataSourceOptions" :key="source.value" :value="source.value"
              :label="source.label" />
          </el-select>
        </el-form-item>

        <el-form-item class="filter-actions">
          <el-button type="primary" :loading="loading" native-type="submit">
            <el-icon>
              <Search />
            </el-icon>查询
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
      <p class="filter-note">默认管报包含全部实际来源，财报扣除“管理调整”；两套来源均可单独调整，清空表示全选。</p>
    </el-card>

    <template v-if="analysisResult">
      <el-row :gutter="12" class="summary-row">
        <el-col :xs="24" :sm="8">
          <el-card shadow="never" class="summary-card">
            <span class="summary-label">管报累计</span>
            <strong>{{ formatAmount(currentDimension.total.ytd_management_report) }}</strong>
            <small>1 月至 {{ query.month }} 月 · {{ amountUnitLabel }}</small>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="8">
          <el-card shadow="never" class="summary-card">
            <span class="summary-label">财报累计</span>
            <strong>{{ formatAmount(currentDimension.total.ytd_financial_report) }}</strong>
            <small>1 月至 {{ query.month }} 月 · {{ amountUnitLabel }}</small>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="8">
          <el-card shadow="never" class="summary-card summary-card--variance">
            <span class="summary-label">累计差额</span>
            <strong>{{ formatAmount(currentDimension.total.ytd_variance) }}</strong>
            <small>管报 − 财报</small>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never" class="analysis-card">
        <template #header>
          <div class="card-heading">
            <div><span class="section-index">02</span><strong>按科目管财差异</strong></div>
            <span class="card-note">管理一级 → 二级 → 三级 → 会计科目</span>
          </div>
        </template>

        <section class="table-section">
          <div class="table-heading">
            <div><span class="section-index">A</span><strong>管报 / 财报对照</strong></div>
            <span>{{ query.year }} 年 · 截至 {{ query.month }} 月</span>
          </div>
          <el-table :data="subjectRows" row-key="id" border stripe default-expand-all
            :tree-props="{ children: 'children' }" :indent="18" show-summary :summary-method="varianceSummary"
            class="analysis-table">
            <el-table-column label="序号" width="160" fixed="left" align="center">
              <template #default="{ row }"><span class="sequence-value">{{ getSequence(row.id) }}</span></template>
            </el-table-column>
            <el-table-column label="管理分类 / 会计科目" min-width="140" fixed="left">
              <template #default="{ row }">
                <DimensionCell :row="row" />
              </template>
            </el-table-column>
            <el-table-column label="当月" align="center" header-align="center">
              <el-table-column prop="current_management_report" label="管报" width="148" align="right">
                <template #default="{ row }">{{ formatAmount(row.current_management_report) }}</template>
              </el-table-column>
              <el-table-column prop="current_financial_report" label="财报" width="148" align="right">
                <template #default="{ row }">{{ formatAmount(row.current_financial_report) }}</template>
              </el-table-column>
              <el-table-column prop="current_variance" label="差额" width="148" align="right">
                <template #default="{ row }"><span :class="varianceClass(row.current_variance)">{{
                  formatAmount(row.current_variance) }}</span></template>
              </el-table-column>
            </el-table-column>
            <el-table-column label="累计" align="center" header-align="center">
              <el-table-column prop="ytd_management_report" label="管报累计" width="148" align="right">
                <template #default="{ row }">{{ formatAmount(row.ytd_management_report) }}</template>
              </el-table-column>
              <el-table-column prop="ytd_financial_report" label="财报累计" width="148" align="right">
                <template #default="{ row }">{{ formatAmount(row.ytd_financial_report) }}</template>
              </el-table-column>
              <el-table-column prop="ytd_variance" label="累计差额" width="148" align="right">
                <template #default="{ row }"><span :class="varianceClass(row.ytd_variance)">{{
                  formatAmount(row.ytd_variance) }}</span></template>
              </el-table-column>
            </el-table-column>
          </el-table>
        </section>
      </el-card>
    </template>

    <el-empty v-else-if="!loading" description="请先选择分析口径并查询" class="empty-state" />
  </section>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue'
import { Refresh, Search } from '@element-plus/icons-vue'

import AccountingSubjectAPI, { type AccountingSubjectCategoryOption } from '@/api/module_dimension/accounting_subject'
import CompanyAPI, { type CompanyOption } from '@/api/module_dimension/company'
import type { DeptTable } from '@/api/module_system/dept'
import ManagementFinanceVarianceAPI, {
  type ManagementFinanceVarianceQuery,
  type ManagementFinanceVarianceResult,
  type ManagementFinanceVarianceRow,
} from '@/api/module_financial/management_finance_variance'
import { COST_CENTER_FUNCTION_SCOPE_DICT_TYPE, fetchDictOptions, type DictOption } from '@/utils/dict'
import { getPreviousMonthPeriod } from '@/utils'

defineOptions({ name: 'ManagementFinanceVariance' })

const monthOptions = Array.from({ length: 12 }, (_, index) => index + 1)
const currentYear = new Date().getFullYear()
const yearOptions = Array.from({ length: 5 }, (_, index) => currentYear - 2 + index)
const dataSourceOptions = [
  { value: 'SAP原始明细', label: 'SAP原始明细' },
  { value: '单体财报调整', label: '单体财报调整' },
  { value: '合并财报调整', label: '合并财报调整' },
  { value: '管理调整', label: '管理调整项目' },
]
const allSourceValues = dataSourceOptions.map((item) => item.value)
const financialDefaultSourceValues = allSourceValues.filter((value) => value !== '管理调整')
const defaultPeriod = getPreviousMonthPeriod()

const loading = ref(false)
const amountUnit = ref<'wan' | 'yuan'>('wan')
const analysisResult = ref<ManagementFinanceVarianceResult>()
const companyOptions = ref<CompanyOption[]>([])
const departmentOptions = ref<DeptTable[]>([])
const categoryOptions = ref<AccountingSubjectCategoryOption[]>([])
const functionScopeOptions = ref<DictOption[]>([])

const query = reactive<ManagementFinanceVarianceQuery>({
  year: defaultPeriod.year,
  month: defaultPeriod.month,
  company_ids: [],
  department_ids: [],
  function_scopes: [],
  management_category_paths: [],
  management_data_source_categories: [...allSourceValues],
  financial_data_source_categories: [...financialDefaultSourceValues],
})

const departmentCascaderProps = {
  value: 'id',
  label: 'name',
  children: 'children',
  multiple: true,
  checkStrictly: true,
  emitPath: false,
}
const categoryCascaderProps = { multiple: true, checkStrictly: true, emitPath: true }

const DimensionCell = defineComponent({
  props: { row: { type: Object as () => ManagementFinanceVarianceRow, required: true } },
  setup(props) {
    return () => h('div', { class: ['dimension-cell', `dimension-cell--${props.row.node_type}`] }, [
      h('div', { class: 'dimension-copy' }, [
        h('strong', props.row.label),
        props.row.code ? h('small', props.row.code) : null,
      ]),
    ])
  },
})

const currentDimension = computed(() => analysisResult.value!.subject)
const subjectRows = computed(() => analysisResult.value?.subject.rows || [])
const amountUnitLabel = computed(() => amountUnit.value === 'wan' ? '单位：万元' : '单位：元')
const sequenceMap = computed(() => {
  const map = new Map<string, string>()

  function visit(rows: ManagementFinanceVarianceRow[], parentSequence = '') {
    rows.forEach((row, index) => {
      const sequence = parentSequence ? `${parentSequence}.${index + 1}` : `${index + 1}`
      map.set(row.id, sequence)
      if (row.children?.length) visit(row.children, sequence)
    })
  }

  visit(subjectRows.value)
  return map
})

function getSequence(id: string) {
  return sequenceMap.value.get(id) || ''
}

function toNumber(value: number | string | null | undefined) {
  const number = Number(value ?? 0)
  return Number.isFinite(number) ? number : 0
}

function formatAmount(value: number | string | null | undefined) {
  const number = toNumber(value) / (amountUnit.value === 'wan' ? 10000 : 1)
  return number.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function varianceClass(value: number | string | null | undefined) {
  const number = toNumber(value)
  return number > 0 ? 'variance-over' : number < 0 ? 'variance-under' : ''
}

function varianceSummary({ columns }: { columns: Array<{ property?: string }> }) {
  const total = currentDimension.value?.total
  if (!total) return columns.map(() => '')
  const values: Record<string, string> = {
    current_management_report: formatAmount(total.current_management_report),
    current_financial_report: formatAmount(total.current_financial_report),
    current_variance: formatAmount(total.current_variance),
    ytd_management_report: formatAmount(total.ytd_management_report),
    ytd_financial_report: formatAmount(total.ytd_financial_report),
    ytd_variance: formatAmount(total.ytd_variance),
  }
  return columns.map((column, index) => index === 1 ? '合计' : values[column.property || ''] || '')
}

async function loadOptions() {
  const [functionScopeResponse, companyResponse, departmentResponse, categoryResponse] = await Promise.all([
    fetchDictOptions(COST_CENTER_FUNCTION_SCOPE_DICT_TYPE),
    CompanyAPI.listCompanyOptions(),
    ManagementFinanceVarianceAPI.departments(),
    AccountingSubjectAPI.categoryOptions(),
  ])
  functionScopeOptions.value = functionScopeResponse
  companyOptions.value = companyResponse.data.data || []
  departmentOptions.value = departmentResponse.data.data || []
  categoryOptions.value = categoryResponse.data.data || []
}

async function loadAnalysis() {
  loading.value = true
  try {
    const response = await ManagementFinanceVarianceAPI.query({
      ...query,
      company_ids: query.company_ids?.length ? query.company_ids : [],
      department_ids: query.department_ids?.length ? query.department_ids : [],
      function_scopes: query.function_scopes?.length ? query.function_scopes : [],
      management_category_paths: query.management_category_paths?.length ? query.management_category_paths : [],
      management_data_source_categories: query.management_data_source_categories?.length
        ? query.management_data_source_categories : [],
      financial_data_source_categories: query.financial_data_source_categories?.length
        ? query.financial_data_source_categories : [],
    })
    analysisResult.value = response.data.data
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  return loadAnalysis()
}

function handleReset() {
  const previousPeriod = getPreviousMonthPeriod()
  query.year = previousPeriod.year
  query.month = previousPeriod.month
  query.company_ids = []
  query.department_ids = []
  query.function_scopes = []
  query.management_category_paths = []
  query.management_data_source_categories = [...allSourceValues]
  query.financial_data_source_categories = [...financialDefaultSourceValues]
  return loadAnalysis()
}

onMounted(async () => {
  loading.value = true
  try {
    await loadOptions()
    await loadAnalysis()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped lang="scss">
.analysis-page {
  min-height: 100%;
  padding: 14px 4px 36px;
  color: var(--app-text);
  font-variant-numeric: tabular-nums;
}

.page-heading,
.card-heading,
.heading-actions,
.table-heading {
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
.card-note,
.filter-note,
.table-heading>span {
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

.filter-card,
.analysis-card {
  margin-top: 16px;
  border-radius: 0;
}

.card-heading {
  justify-content: space-between;
  gap: 16px;
}

.card-heading>div,
.table-heading>div {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-grid {
  display: grid;
  grid-template-columns: .7fr .75fr 1fr 1.35fr 1.1fr 1.2fr 1.25fr 1.25fr auto;
  gap: 0 12px;
  align-items: end;
}

.filter-control,
.unit-switch {
  width: 100%;
}

.filter-actions {
  white-space: nowrap;
}

.filter-note {
  margin: 12px 0 0;
  font-size: 12px;
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
  font-size: clamp(22px, 2.3vw, 30px);
  line-height: 1;
}

.summary-card small {
  font-size: 11px;
}

.summary-card--variance strong {
  color: var(--el-color-danger);
}

.table-section {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid var(--app-border);
}

.table-section:first-child {
  margin-top: 0;
  padding-top: 0;
  border-top: 0;
}

.table-heading {
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.analysis-table {
  width: 100%;
  --el-table-header-bg-color: #f7f9fc;
  --el-table-border-color: var(--app-border);
  --el-table-row-hover-bg-color: #f8fbff;
}

.analysis-table :deep(.el-table__cell) {
  padding: 3px 0;
}

.analysis-table :deep(.cell) {
  display: flex;
  align-items: center;
  min-height: 28px;
  line-height: 28px;
}

.analysis-table :deep(.el-table__header-wrapper .cell),
.analysis-table :deep(.el-table__fixed-header-wrapper .cell) {
  justify-content: center;
  text-align: center;
}

.analysis-table :deep(.el-table__body .is-right .cell),
.analysis-table :deep(.el-table__footer .is-right .cell),
.analysis-table :deep(.el-table__fixed-footer-wrapper .is-right .cell) {
  justify-content: flex-end;
  text-align: right;
}

.analysis-table :deep(.el-table__expand-icon),
.analysis-table :deep(.el-table__placeholder) {
  flex: 0 0 18px;
  margin-right: 5px;
}

.analysis-table :deep(.el-table__expand-icon) {
  margin-left: 0;
}

.analysis-table :deep(.el-table__footer-wrapper td) {
  background: #eef5ff;
  color: var(--el-color-primary);
  font-weight: 700;
}

.sequence-value {
  display: block;
  width: 100%;
  color: var(--app-muted);
  font-family: var(--app-mono);
  font-size: 12px;
  text-align: center;
}

.dimension-cell {
  display: flex;
  align-items: center;
  min-width: 0;
  flex: 1;
}

.dimension-copy {
  display: flex;
  min-width: 0;
  align-items: baseline;
  gap: 8px;
}

.dimension-copy strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dimension-copy small {
  flex: 0 0 auto;
  color: var(--app-muted);
  font-family: var(--app-mono);
  font-size: 11px;
  line-height: 1;
}

.variance-over {
  color: var(--el-color-danger);
  font-weight: 600;
}

.variance-under {
  color: var(--el-color-success);
  font-weight: 600;
}

@media (max-width: 1500px) {
  .filter-grid {
    grid-template-columns: repeat(4, minmax(160px, 1fr));
  }
}

@media (max-width: 760px) {

  .page-heading,
  .card-heading,
  .table-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .heading-actions {
    justify-content: flex-start;
  }

  .filter-grid {
    grid-template-columns: 1fr;
  }

  .unit-switch {
    width: auto;
  }
}
</style>
