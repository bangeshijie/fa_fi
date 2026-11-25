import request from '@/utils/request'
import type { DeptTable } from '@/api/module_system/dept'

const API_PATH = '/financial/expense-analysis'

const ExpenseAnalysisAPI = {
  departments() {
    return request<ApiResponse<DeptTable[]>>({
      url: `${API_PATH}/departments`,
      method: 'get',
    })
  },

  query(body: ExpenseAnalysisQuery) {
    return request<ApiResponse<ExpenseAnalysisResult>>({
      url: `${API_PATH}/query`,
      method: 'post',
      data: body,
    })
  },
}

export default ExpenseAnalysisAPI

export interface ExpenseAnalysisQuery {
  budget_version: string
  year: number
  month: number
  company_ids?: number[]
  department_ids?: number[]
  function_scopes?: string[]
  data_source_categories?: string[]
}

export interface ExpenseAnalysisRow {
  id: string
  label: string
  code?: string | null
  node_type: 'department' | 'cost_center' | 'accounting_subject' | 'control_department'
  level: number
  control_person?: string | null
  current_actual: number | string
  current_budget: number | string
  current_variance: number | string
  current_completion_rate?: number | string | null
  prior_year_current_completion_rate?: number | string | null
  ytd_actual: number | string
  ytd_budget: number | string
  ytd_variance: number | string
  ytd_completion_rate?: number | string | null
  prior_year_ytd_completion_rate?: number | string | null
  annual_budget: number | string
  annual_completion_rate?: number | string | null
  actual_months: Array<number | string>
  budget_months: Array<number | string>
  children?: ExpenseAnalysisRow[]
}

export interface ExpenseAnalysisDimension {
  rows: ExpenseAnalysisRow[]
  total: ExpenseAnalysisRow
}

export interface ExpenseAnalysisResult {
  currency: 'RMB'
  amount_unit: '元'
  available_data_source_categories: string[]
  department: ExpenseAnalysisDimension
  subject: ExpenseAnalysisDimension
  control_department: ExpenseAnalysisDimension
}
