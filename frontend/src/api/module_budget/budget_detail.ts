import request from '@/utils/request'

const API_PATH = '/budget/budget-detail'

const BudgetDetailAPI = {
  list(query?: BudgetDetailPageQuery) {
    return request<ApiResponse<BudgetDetailPageResult>>({
      url: `${API_PATH}/list`,
      method: 'get',
      params: query,
    })
  },

  detail(id: number) {
    return request<ApiResponse<BudgetDetailTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: 'get',
    })
  },

  create(body: BudgetDetailForm) {
    return request<ApiResponse<BudgetDetailTable>>({
      url: `${API_PATH}/create`,
      method: 'post',
      data: body,
    })
  },

  update(id: number, body: BudgetDetailForm) {
    return request<ApiResponse<BudgetDetailTable>>({
      url: `${API_PATH}/update/${id}`,
      method: 'put',
      data: body,
    })
  },

  delete(ids: number[]) {
    return request<ApiResponse<null>>({
      url: `${API_PATH}/delete`,
      method: 'delete',
      data: ids,
    })
  },

  export(query: BudgetDetailExportQuery) {
    return request<Blob>({
      url: `${API_PATH}/export`,
      method: 'post',
      params: query,
      responseType: 'blob',
    })
  },

  downloadTemplate() {
    return request<Blob>({
      url: `${API_PATH}/import/template`,
      method: 'post',
      responseType: 'blob',
    })
  },

  importData(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    return request<ApiResponse<BudgetDetailImportResult>>({
      url: `${API_PATH}/import/data`,
      method: 'post',
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

export default BudgetDetailAPI

export interface BudgetDetailPageQuery extends PageQuery {
  budget_version?: string
  year?: number
  company_id?: number
  accounting_subject_ids?: number[]
  cost_center_ids?: number[]
  department_ids?: number[]
  belonging_months?: number[]
  data_source_category?: string[]
}

export type BudgetDetailExportQuery = Omit<BudgetDetailPageQuery, 'page_no' | 'page_size'>

export interface BudgetDetailPageResult extends PageResult<BudgetDetailTable> {
  amount_sum: number | string
}

export interface BudgetDetailTable extends BaseType {
  id: number
  budget_version: string
  year: number
  company_id: number
  company_code?: string | null
  company_name?: string | null
  accounting_subject_id: number
  accounting_subject_code?: string | null
  accounting_subject_name?: string | null
  cost_center_id?: number | null
  cost_center_code?: string | null
  cost_center_name?: string | null
  belonging_month: number
  currency: string
  amount: number | string
  budget_text?: string | null
  data_source_category: string
  source_description?: string | null
}

export interface BudgetDetailForm {
  budget_version?: string
  year?: number
  company_id?: number
  accounting_subject_id?: number
  cost_center_id?: number | null
  belonging_month?: number
  currency?: string
  amount?: number
  budget_text?: string | null
  data_source_category?: string
  source_description?: string | null
}

export interface BudgetDetailImportError {
  row_number: number
  budget_version?: string | null
  reason: string
}

export interface BudgetDetailImportResult {
  total_count: number
  success_count: number
  created_count: number
  failed_count: number
  errors: BudgetDetailImportError[]
  errors_truncated: boolean
}
