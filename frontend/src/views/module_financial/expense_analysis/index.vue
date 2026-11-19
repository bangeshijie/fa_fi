<template>
  <section class="analysis-page">
    <header class="page-heading">
      <div>
        <div class="heading-title-row">
          <h2>费用分析</h2>
          <p class="eyebrow">FINANCIAL / EXPENSE ANALYSIS</p>
        </div>
        <p class="heading-copy">按部门和会计科目聚合预算、实际及差额，实际数据包含调整数据。</p>
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
        <el-form-item label="预算版本" required>
          <el-select v-model="query.budget_version" filterable class="filter-control" placeholder="请选择预算版本">
            <el-option v-for="option in budgetVersionOptions" :key="option.dict_value" :value="option.dict_value"
              :label="`${option.dict_value} ${option.dict_label || ''}`" />
          </el-select>
        </el-form-item>

        <el-form-item label="年度" required>
          <el-select v-model="query.year" class="year-control">
            <el-option v-for="year in yearOptions" :key="year" :value="year" :label="`${year} 年`" />
          </el-select>
        </el-form-item>

        <el-form-item label="截至月份" required>
          <el-select v-model="query.month" class="month-control">
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
            clearable filterable collapse-tags collapse-tags-tooltip class="wide-control" placeholder="全部部门，选择上级包含下级" />
        </el-form-item>

        <el-form-item label="职能范围">
          <el-select v-model="query.function_scopes" multiple collapse-tags collapse-tags-tooltip clearable filterable
            class="source-control" placeholder="全部职能范围">
            <el-option v-for="option in functionScopeOptions" :key="option.dict_value" :value="option.dict_value"
              :label="`${option.dict_value} ${option.dict_label || ''}`" />
          </el-select>
        </el-form-item>

        <el-form-item label="管理分类">
          <el-cascader v-model="query.management_category_paths" :options="categoryOptions"
            :props="categoryCascaderProps" clearable filterable collapse-tags collapse-tags-tooltip
            class="category-control" placeholder="全部管理分类" />
        </el-form-item>

        <el-form-item label="实际数据来源">
          <el-select v-model="query.data_source_categories" multiple collapse-tags collapse-tags-tooltip clearable
            class="source-control" placeholder="全部来源">
            <el-option v-for="source in dataSourceOptions" :key="source" :value="source" :label="source" />
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
      <p class="filter-note">数据来源分类只筛选实际费用；预算按选定预算版本汇总全部人民币预算数据。</p>
    </el-card>

    <template v-if="analysisResult">
      <el-row :gutter="12" class="summary-row">
        <el-col :xs="12" :sm="6" :lg="3">
          <el-card shadow="never" class="summary-card">
            <span class="summary-label">全年预算</span>
            <strong>{{ formatAmount(currentDimension.total.annual_budget) }}</strong>

            <small>{{ amountUnitLabel }}</small>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6" :lg="3">
          <el-card shadow="never" class="summary-card">
            <span class="summary-label">截至当月实际</span>
            <strong>{{ formatAmount(currentDimension.total.ytd_actual) }}</strong>
            <small>1 月至 {{ query.month }} 月</small>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6" :lg="3">
          <el-card shadow="never" class="summary-card">
            <span class="summary-label">截至当月预算</span>
            <strong>{{ formatAmount(currentDimension.total.ytd_budget) }}</strong>
            <small>选定预算版本</small>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6" :lg="3">
          <el-card shadow="never" class="summary-card summary-card--variance">
            <span class="summary-label">累计差额</span>
            <strong>{{ formatAmount(currentDimension.total.ytd_variance) }}</strong>
            <small>实际 - 预算</small>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6" :lg="3">
          <el-card shadow="never" class="summary-card">
            <span class="summary-label">累计完成率</span>
            <strong>{{ formatRate(currentDimension.total.ytd_completion_rate) }}</strong>
            <small>累计实际 ÷ 累计预算</small>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never" class="analysis-card">
        <template #header>
          <div class="card-heading">
            <div><span class="section-index">02</span><strong>费用汇总</strong></div>
            <span class="card-note">差额为实际减预算，正数表示超预算</span>
          </div>
        </template>

        <el-tabs v-model="activeView" class="analysis-tabs">
          <el-tab-pane name="department">
            <template #label><span class="tab-label">按部门 <em>{{ departmentRows.length }} 个根节点</em></span></template>
            <section class="table-section">
              <div class="table-heading">
                <div><span class="section-index">A</span><strong>预实分析</strong></div>
                <span>部门层级</span>
              </div>
              <el-table :data="departmentRows" row-key="id" border stripe default-expand-all
                :tree-props="{ children: 'children' }" :indent="18" show-summary :summary-method="varianceSummary"
                class="analysis-table">
                <el-table-column label="序号" width="160" fixed="left" align="center">
                  <template #default="{ row }"><span class="sequence-value">{{ getSequence('department', row.id)
                  }}</span></template>
                </el-table-column>
                <el-table-column label="部门" min-width="140" fixed="left">
                  <template #default="{ row }">
                    <DimensionCell :row="row" />
                  </template>
                </el-table-column>
                <el-table-column label="当月" align="center" header-align="center">
                  <el-table-column prop="current_actual" label="实际" width="124" align="right"><template
                      #default="{ row }">{{ formatAmount(row.current_actual) }}</template></el-table-column>
                  <el-table-column prop="current_budget" label="预算" width="124" align="right"><template
                      #default="{ row }">{{ formatAmount(row.current_budget) }}</template></el-table-column>
                  <el-table-column prop="current_variance" label="差额" width="124" align="right"><template
                      #default="{ row }"><span :class="varianceClass(row.current_variance)">{{
                        formatAmount(row.current_variance) }}</span></template></el-table-column>
                  <el-table-column prop="current_completion_rate" label="完成率" width="104" align="right"><template
                      #default="{ row }">{{ formatRate(row.current_completion_rate) }}</template></el-table-column>
                  <el-table-column prop="prior_year_current_completion_rate" label="同期" width="104"
                    align="right"><template #default="{ row }">{{ formatRate(row.prior_year_current_completion_rate)
                      }}</template></el-table-column>
                </el-table-column>
                <el-table-column label="累计" align="center" header-align="center">
                  <el-table-column prop="ytd_actual" label="实际累计" width="124" align="right"><template
                      #default="{ row }">{{ formatAmount(row.ytd_actual) }}</template></el-table-column>
                  <el-table-column prop="ytd_budget" label="预算累计" width="124" align="right"><template
                      #default="{ row }">{{ formatAmount(row.ytd_budget) }}</template></el-table-column>
                  <el-table-column prop="ytd_variance" label="差额累计" width="124" align="right"><template
                      #default="{ row }"><span :class="varianceClass(row.ytd_variance)">{{
                        formatAmount(row.ytd_variance) }}</span></template></el-table-column>
                  <el-table-column prop="ytd_completion_rate" label="完成率累计" width="112" align="right"><template
                      #default="{ row }">{{ formatRate(row.ytd_completion_rate) }}</template></el-table-column>
                  <el-table-column prop="prior_year_ytd_completion_rate" label="同期累计" width="112"
                    align="right"><template #default="{ row }">{{ formatRate(row.prior_year_ytd_completion_rate)
                      }}</template></el-table-column>
                </el-table-column>
                <el-table-column label="年度" align="center" header-align="center">
                  <el-table-column prop="annual_budget" label="全年预算" width="124" align="right"><template
                      #default="{ row }">{{ formatAmount(row.annual_budget) }}</template></el-table-column>
                  <el-table-column prop="annual_completion_rate" label="全年完成率" width="116" align="right"><template
                      #default="{ row }">{{ formatRate(row.annual_completion_rate) }}</template></el-table-column>
                </el-table-column>
              </el-table>
            </section>

            <section class="trend-chart-section">
              <div class="table-heading">
                <div><span class="section-index">B</span><strong>预算 / 实际趋势</strong></div>
                <span>部门合计 · 1 月至 12 月</span>
              </div>
              <IndustrialChart :option="trendOption" height="250px" :loading="loading" :is-empty="!hasTrendData" />
            </section>

            <section class="table-section">
              <div class="table-heading">
                <div><span class="section-index">C</span><strong>实际趋势</strong></div><span>1 月至 12 月实际金额</span>
              </div>
              <el-table :data="departmentRows" row-key="id" border stripe default-expand-all
                :tree-props="{ children: 'children' }" :indent="18" show-summary :summary-method="actualSummary"
                class="analysis-table monthly-table">
                <el-table-column label="序号" width="160" fixed="left" align="center">
                  <template #default="{ row }"><span class="sequence-value">{{ getSequence('department', row.id)
                  }}</span></template>
                </el-table-column>
                <el-table-column label="部门" min-width="140" fixed="left"><template #default="{ row }">
                    <DimensionCell :row="row" />
                  </template></el-table-column>
                <el-table-column v-for="month in monthOptions" :key="month" :prop="`actual_month_${month - 1}`"
                  :label="`${month}月`" width="112" align="right"><template #default="{ row }">{{
                    formatAmount(row.actual_months[month - 1]) }}</template></el-table-column>
              </el-table>
            </section>

            <section class="table-section">
              <div class="table-heading">
                <div><span class="section-index">D</span><strong>预算趋势</strong></div><span>{{ budgetVersionLabel }} · 1
                  月至 12
                  月</span>
              </div>
              <el-table :data="departmentRows" row-key="id" border stripe default-expand-all
                :tree-props="{ children: 'children' }" :indent="18" show-summary :summary-method="budgetSummary"
                class="analysis-table monthly-table">
                <el-table-column label="序号" width="160" fixed="left" align="center">
                  <template #default="{ row }"><span class="sequence-value">{{ getSequence('department', row.id)
                  }}</span></template>
                </el-table-column>
                <el-table-column label="部门" min-width="140" fixed="left"><template #default="{ row }">
                    <DimensionCell :row="row" />
                  </template></el-table-column>
                <el-table-column v-for="month in monthOptions" :key="month" :prop="`budget_month_${month - 1}`"
                  :label="`${month}月`" width="112" align="right"><template #default="{ row }">{{
                    formatAmount(row.budget_months[month - 1]) }}</template></el-table-column>
              </el-table>
            </section>
          </el-tab-pane>

          <el-tab-pane name="subject">
            <template #label><span class="tab-label">按科目 <em>{{ subjectRows.length }} 个根节点</em></span></template>
            <section class="table-section">
              <div class="table-heading">
                <div><span class="section-index">A</span><strong>预实分析</strong></div><span>管理一级 → 二级 → 三级 → 会计科目</span>
              </div>
              <el-table :data="subjectRows" row-key="id" border stripe default-expand-all
                :tree-props="{ children: 'children' }" :indent="18" show-summary :summary-method="varianceSummary"
                class="analysis-table">
                <el-table-column label="序号" width="160" fixed="left" align="center">
                  <template #default="{ row }"><span class="sequence-value">{{ getSequence('subject', row.id)
                  }}</span></template>
                </el-table-column>
                <el-table-column label="管理分类 / 会计科目" min-width="140" fixed="left"><template #default="{ row }">
                    <DimensionCell :row="row" />
                  </template></el-table-column>
                <el-table-column label="当月" align="center" header-align="center">
                  <el-table-column prop="current_actual" label="实际" width="124" align="right"><template
                      #default="{ row }">{{ formatAmount(row.current_actual) }}</template></el-table-column>
                  <el-table-column prop="current_budget" label="预算" width="124" align="right"><template
                      #default="{ row }">{{ formatAmount(row.current_budget) }}</template></el-table-column>
                  <el-table-column prop="current_variance" label="差额" width="124" align="right"><template
                      #default="{ row }"><span :class="varianceClass(row.current_variance)">{{
                        formatAmount(row.current_variance) }}</span></template></el-table-column>
                  <el-table-column prop="current_completion_rate" label="完成率" width="104" align="right"><template
                      #default="{ row }">{{ formatRate(row.current_completion_rate) }}</template></el-table-column>
                  <el-table-column prop="prior_year_current_completion_rate" label="同期" width="104"
                    align="right"><template #default="{ row }">{{ formatRate(row.prior_year_current_completion_rate)
                      }}</template></el-table-column>
                </el-table-column>
                <el-table-column label="累计" align="center" header-align="center">
                  <el-table-column prop="ytd_actual" label="累计实际" width="124" align="right"><template
                      #default="{ row }">{{ formatAmount(row.ytd_actual) }}</template></el-table-column>
                  <el-table-column prop="ytd_budget" label="预算累计" width="124" align="right"><template
                      #default="{ row }">{{ formatAmount(row.ytd_budget) }}</template></el-table-column>
                  <el-table-column prop="ytd_variance" label="累计差额" width="124" align="right"><template
                      #default="{ row }"><span :class="varianceClass(row.ytd_variance)">{{
                        formatAmount(row.ytd_variance) }}</span></template></el-table-column>
                  <el-table-column prop="ytd_completion_rate" label="累计完成率" width="112" align="right"><template
                      #default="{ row }">{{ formatRate(row.ytd_completion_rate) }}</template></el-table-column>
                  <el-table-column prop="prior_year_ytd_completion_rate" label="同期累计" width="112"
                    align="right"><template #default="{ row }">{{ formatRate(row.prior_year_ytd_completion_rate)
                      }}</template></el-table-column>
                </el-table-column>
                <el-table-column label="年度" align="center" header-align="center">
                  <el-table-column prop="annual_budget" label="全年预算" width="124" align="right"><template
                      #default="{ row }">{{ formatAmount(row.annual_budget) }}</template></el-table-column>
                  <el-table-column prop="annual_completion_rate" label="全年完成率" width="116" align="right"><template
                      #default="{ row }">{{ formatRate(row.annual_completion_rate) }}</template></el-table-column>
                </el-table-column>
              </el-table>
            </section>

            <section class="trend-chart-section">
              <div class="table-heading">
                <div><span class="section-index">B</span><strong>预算 / 实际趋势</strong></div>
                <span>科目合计 · 1 月至 12 月</span>
              </div>
              <IndustrialChart :option="trendOption" height="250px" :loading="loading" :is-empty="!hasTrendData" />
            </section>

            <section class="table-section">
              <div class="table-heading">
                <div><span class="section-index">C</span><strong>实际趋势</strong></div><span>1 月至 12 月实际金额</span>
              </div>
              <el-table :data="subjectRows" row-key="id" border stripe default-expand-all
                :tree-props="{ children: 'children' }" :indent="18" show-summary :summary-method="actualSummary"
                class="analysis-table monthly-table">
                <el-table-column label="序号" width="160" fixed="left" align="center">
                  <template #default="{ row }"><span class="sequence-value">{{ getSequence('subject', row.id)
                  }}</span></template>
                </el-table-column>
                <el-table-column label="管理分类 / 会计科目" min-width="140" fixed="left"><template #default="{ row }">
                    <DimensionCell :row="row" />
                  </template></el-table-column>
                <el-table-column v-for="month in monthOptions" :key="month" :prop="`actual_month_${month - 1}`"
                  :label="`${month}月`" width="112" align="right"><template #default="{ row }">{{
                    formatAmount(row.actual_months[month - 1]) }}</template></el-table-column>
              </el-table>
            </section>

            <section class="table-section">
              <div class="table-heading">
                <div><span class="section-index">D</span><strong>预算趋势</strong></div><span>{{ budgetVersionLabel }} · 1
                  月至 12
                  月</span>
              </div>
              <el-table :data="subjectRows" row-key="id" border stripe default-expand-all
                :tree-props="{ children: 'children' }" :indent="18" show-summary :summary-method="budgetSummary"
                class="analysis-table monthly-table">
                <el-table-column label="序号" width="160" fixed="left" align="center">
                  <template #default="{ row }"><span class="sequence-value">{{ getSequence('subject', row.id)
                  }}</span></template>
                </el-table-column>
                <el-table-column label="管理分类 / 会计科目" min-width="140" fixed="left"><template #default="{ row }">
                    <DimensionCell :row="row" />
                  </template></el-table-column>
                <el-table-column v-for="month in monthOptions" :key="month" :prop="`budget_month_${month - 1}`"
                  :label="`${month}月`" width="112" align="right"><template #default="{ row }">{{
                    formatAmount(row.budget_months[month - 1]) }}</template></el-table-column>
              </el-table>
            </section>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </template>

    <el-empty v-else-if="!loading" description="请先选择分析口径并查询" class="empty-state" />
  </section>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import type { EChartsOption } from 'echarts'

import AccountingSubjectAPI, { type AccountingSubjectCategoryOption } from '@/api/module_dimension/accounting_subject'
import CompanyAPI, { type CompanyOption } from '@/api/module_dimension/company'
import type { DeptTable } from '@/api/module_system/dept'
import ExpenseAnalysisAPI, { type ExpenseAnalysisQuery, type ExpenseAnalysisResult, type ExpenseAnalysisRow } from '@/api/module_financial/expense_analysis'
import IndustrialChart from '@/components/charts/IndustrialChart.vue'
import { BUDGET_VERSION_DICT_TYPE, COST_CENTER_FUNCTION_SCOPE_DICT_TYPE, fetchDictOptions, getDefaultDictValue, type DictOption } from '@/utils/dict'
import { getPreviousMonthPeriod } from '@/utils'

defineOptions({ name: 'ExpenseAnalysis' })

const monthOptions = Array.from({ length: 12 }, (_, index) => index + 1)
const currentYear = new Date().getFullYear()
const yearOptions = Array.from({ length: 5 }, (_, index) => currentYear - 2 + index)
const dataSourceOptions = ['SAP原始明细', '单体财报调整', '合并财报调整', '管理调整']

const defaultPeriod = getPreviousMonthPeriod()

const loading = ref(false)
const activeView = ref<'department' | 'subject'>('department')
const amountUnit = ref<'wan' | 'yuan'>('wan')
const analysisResult = ref<ExpenseAnalysisResult>()
const companyOptions = ref<CompanyOption[]>([])
const departmentOptions = ref<DeptTable[]>([])
const categoryOptions = ref<AccountingSubjectCategoryOption[]>([])
const budgetVersionOptions = ref<DictOption[]>([])
const functionScopeOptions = ref<DictOption[]>([])
const defaultBudgetVersion = ref('')

const query = reactive<ExpenseAnalysisQuery>({
  budget_version: '',
  year: defaultPeriod.year,
  month: defaultPeriod.month,
  company_ids: [],
  department_ids: [],
  function_scopes: [],
  management_category_paths: [],
  data_source_categories: [...dataSourceOptions],
})

const departmentCascaderProps = {
  value: 'id',
  label: 'name',
  children: 'children',
  multiple: true,
  checkStrictly: true,
  emitPath: false,
}
const categoryCascaderProps = {
  multiple: true,
  checkStrictly: true,
  emitPath: true,
}

const DimensionCell = defineComponent({
  props: { row: { type: Object as () => ExpenseAnalysisRow, required: true } },
  setup(props) {
    return () => h('div', { class: ['dimension-cell', `dimension-cell--${props.row.node_type}`] }, [
      h('div', { class: 'dimension-copy' }, [
        h('strong', props.row.label),
        props.row.code ? h('small', props.row.code) : null,
      ]),
    ])
  },
})

const currentDimension = computed(() => activeView.value === 'department' ? analysisResult.value!.department : analysisResult.value!.subject)
const departmentRows = computed(() => analysisResult.value?.department.rows || [])
const subjectRows = computed(() => analysisResult.value?.subject.rows || [])
function buildSequenceMap(rows: ExpenseAnalysisRow[]) {
  const map = new Map<string, string>()

  function visit(items: ExpenseAnalysisRow[], parentSequence = '') {
    items.forEach((row, index) => {
      const sequence = parentSequence ? `${parentSequence}.${index + 1}` : `${index + 1}`
      map.set(row.id, sequence)
      if (row.children?.length) visit(row.children, sequence)
    })
  }

  visit(rows)
  return map
}

const departmentSequenceMap = computed(() => buildSequenceMap(departmentRows.value))
const subjectSequenceMap = computed(() => buildSequenceMap(subjectRows.value))

function getSequence(dimension: 'department' | 'subject', id: string) {
  const map = dimension === 'department' ? departmentSequenceMap.value : subjectSequenceMap.value
  return map.get(id) || ''
}

const amountUnitLabel = computed(() => amountUnit.value === 'wan' ? '单位：万元' : '单位：元')
const budgetVersionLabel = computed(() => {
  const option = budgetVersionOptions.value.find((item) => item.dict_value === query.budget_version)
  return option ? `${query.budget_version} ${option.dict_label || ''}` : query.budget_version
})

const trendOption = computed<EChartsOption>(() => {
  const total = currentDimension.value?.total
  const unit = amountUnit.value === 'wan' ? '万元' : '元'
  const divisor = amountUnit.value === 'wan' ? 10000 : 1
  const toChartValue = (value: number | string | null | undefined) => toNumber(value) / divisor

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line' },
      valueFormatter: (value) => `${toChartValue(value as number | string).toLocaleString('zh-CN', { maximumFractionDigits: 2 })} ${unit}`,
    },
    legend: {
      top: 2,
      right: 8,
      itemWidth: 18,
      itemHeight: 3,
      textStyle: { color: '#68736c', fontSize: 12 },
    },
    grid: { left: 56, right: 22, top: 34, bottom: 34 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: monthOptions.map((month) => `${month}月`),
      axisLabel: { color: '#68736c' },
      axisLine: { lineStyle: { color: '#d8e0e8' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#68736c',
        formatter: (value: number) => Number(value).toLocaleString('zh-CN', { maximumFractionDigits: 1 }),
      },
      splitLine: { lineStyle: { color: '#e8edf3' } },
    },
    series: [
      {
        type: 'line',
        name: '预算',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: { color: '#f59e0b' },
        lineStyle: { color: '#f59e0b', width: 2 },
        data: monthOptions.map((month) => toChartValue(total?.budget_months[month - 1])),
      },
      {
        type: 'line',
        name: '实际',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: { color: '#1d4ed8' },
        lineStyle: { color: '#1d4ed8', width: 2 },
        data: monthOptions.map((month) => toChartValue(total?.actual_months[month - 1])),
      },
    ],
  }
})

const hasTrendData = computed(() => {
  const total = currentDimension.value?.total
  return Boolean(total && [...total.actual_months, ...total.budget_months].some((value) => toNumber(value) !== 0))
})

function toNumber(value: number | string | null | undefined) {
  const number = Number(value ?? 0)
  return Number.isFinite(number) ? number : 0
}

function formatAmount(value: number | string | null | undefined) {
  const number = toNumber(value) / (amountUnit.value === 'wan' ? 10000 : 1)
  return number.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatRate(value: number | string | null | undefined) {
  if (value == null || value === '') return '—'
  const number = Number(value)
  return Number.isFinite(number) ? `${(number * 100).toFixed(1)}%` : '—'
}

function varianceClass(value: number | string | null | undefined) {
  const number = toNumber(value)
  return number > 0 ? 'variance-over' : number < 0 ? 'variance-under' : ''
}

function summaryFor(total: ExpenseAnalysisRow | undefined, columns: Array<{ property?: string }>, type: 'variance' | 'actual' | 'budget') {
  if (!total) return columns.map(() => '')
  const values: Record<string, string> = { label: '合计' }
  if (type === 'variance') {
    Object.assign(values, {
      current_actual: formatAmount(total.current_actual),
      current_budget: formatAmount(total.current_budget),
      current_variance: formatAmount(total.current_variance),
      current_completion_rate: formatRate(total.current_completion_rate),
      ytd_actual: formatAmount(total.ytd_actual),
      ytd_budget: formatAmount(total.ytd_budget),
      ytd_variance: formatAmount(total.ytd_variance),
      ytd_completion_rate: formatRate(total.ytd_completion_rate),
      annual_budget: formatAmount(total.annual_budget),
      annual_completion_rate: formatRate(total.annual_completion_rate),
    })
  } else {
    monthOptions.forEach((month) => { values[`${type}_month_${month - 1}`] = formatAmount(type === 'actual' ? total.actual_months[month - 1] : total.budget_months[month - 1]) })
  }
  return columns.map((column, index) => index === 1 ? '合计' : values[column.property || ''] || '')
}

function varianceSummary({ columns }: { columns: Array<{ property?: string }> }) {
  return summaryFor(currentDimension.value?.total, columns, 'variance')
}

function actualSummary({ columns }: { columns: Array<{ property?: string }> }) {
  return summaryFor(currentDimension.value?.total, columns, 'actual')
}

function budgetSummary({ columns }: { columns: Array<{ property?: string }> }) {
  return summaryFor(currentDimension.value?.total, columns, 'budget')
}

async function loadOptions() {
  const [budgetResponse, functionScopeResponse, companyResponse, departmentResponse, categoryResponse] = await Promise.all([
    fetchDictOptions(BUDGET_VERSION_DICT_TYPE),
    fetchDictOptions(COST_CENTER_FUNCTION_SCOPE_DICT_TYPE),
    CompanyAPI.listCompanyOptions(),
    ExpenseAnalysisAPI.departments(),
    AccountingSubjectAPI.categoryOptions(),
  ])
  budgetVersionOptions.value = budgetResponse
  functionScopeOptions.value = functionScopeResponse
  companyOptions.value = companyResponse.data.data || []
  departmentOptions.value = departmentResponse.data.data || []
  categoryOptions.value = categoryResponse.data.data || []
  defaultBudgetVersion.value = getDefaultDictValue(budgetResponse) || 'MCB'
  if (!query.budget_version) query.budget_version = defaultBudgetVersion.value
}

async function loadAnalysis() {
  if (!query.budget_version) {
    ElMessage.warning('请选择预算版本')
    return
  }
  loading.value = true
  try {
    const response = await ExpenseAnalysisAPI.query({
      ...query,
      company_ids: query.company_ids?.length ? query.company_ids : [],
      department_ids: query.department_ids?.length ? query.department_ids : [],
      function_scopes: query.function_scopes?.length ? query.function_scopes : [],
      management_category_paths: query.management_category_paths?.length ? query.management_category_paths : [],
      data_source_categories: query.data_source_categories?.length ? query.data_source_categories : [],
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
  query.budget_version = defaultBudgetVersion.value
  query.year = previousPeriod.year
  query.month = previousPeriod.month
  query.company_ids = []
  query.department_ids = []
  query.function_scopes = []
  query.management_category_paths = []
  query.data_source_categories = [...dataSourceOptions]
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
  grid-template-columns: 1.1fr .65fr .55fr 1fr 1.25fr 1.25fr 1.2fr .80fr auto auto;
  gap: 0 12px;
  align-items: end;
}

.filter-control {
  width: 100%;
}

.year-control,
.month-control {
  width: 100%;
}

.wide-control,
.category-control,
.source-control {
  width: 100%;
}

.unit-switch {
  display: flex;
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

.analysis-tabs :deep(.el-tabs__header) {
  margin-bottom: 22px;
}

.tab-label {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
}

.tab-label em {
  color: var(--app-muted);
  font-size: 11px;
  font-style: normal;
  font-weight: 400;
}

.trend-chart-section {
  margin-top: 22px;
  padding: 18px 0 4px;
  border-top: 1px solid var(--app-border);
}

.trend-chart-section :deep(.industrial-chart) {
  min-height: 210px;
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
  margin-bottom: 10px;
  font-size: 13px;
}

.table-heading .section-index {
  min-width: 18px;
}

.analysis-table {
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

.monthly-table :deep(.el-table__body-wrapper) {
  min-height: 92px;
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
  font-weight: 700;
}

.variance-under {
  color: var(--el-color-success);
}

.empty-state {
  padding: 64px 0;
}

@media (max-width: 1500px) {
  .filter-grid {
    grid-template-columns: repeat(4, minmax(150px, 1fr));
  }

  .filter-actions {
    grid-column: span 4;
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

  .filter-grid {
    grid-template-columns: 1fr 1fr;
  }

  .filter-actions {
    grid-column: span 2;
  }

  .table-heading {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
