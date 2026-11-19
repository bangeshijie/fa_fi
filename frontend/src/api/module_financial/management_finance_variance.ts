import request from '@/utils/request'
import type { DeptTable } from '@/api/module_system/dept'

const API_PATH = '/financial/management-finance-variance'

const ManagementFinanceVarianceAPI = {
  departments() {
    return request<ApiResponse<DeptTable[]>>({
      url: `${API_PATH}/departments`,
      method: 'get',
    })
  },

  query(body: ManagementFinanceVarianceQuery) {
    return request<ApiResponse<ManagementFinanceVarianceResult>>({
      url: `${API_PATH}/query`,
      method: 'post',
      data: body,
    })
  },
}

export default ManagementFinanceVarianceAPI

export interface ManagementFinanceVarianceQuery {
  year: number
  month: number
  company_ids?: number[]
  department_ids?: number[]
  function_scopes?: string[]
  management_category_paths?: string[][]
  management_data_source_categories?: string[]
  financial_data_source_categories?: string[]
}

export interface ManagementFinanceVarianceRow {
  id: string
  label: string
  code?: string | null
  node_type: 'category' | 'accounting_subject'
  level: number
  current_management_report: number | string
  current_financial_report: number | string
  current_variance: number | string
  ytd_management_report: number | string
  ytd_financial_report: number | string
  ytd_variance: number | string
  children?: ManagementFinanceVarianceRow[]
}

export interface ManagementFinanceVarianceDimension {
  rows: ManagementFinanceVarianceRow[]
  total: ManagementFinanceVarianceRow
}

export interface ManagementFinanceVarianceResult {
  currency: 'RMB'
  amount_unit: '元'
  available_data_source_categories: string[]
  subject: ManagementFinanceVarianceDimension
}
