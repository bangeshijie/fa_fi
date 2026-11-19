import request from '@/utils/request'

const API_PATH = '/financial/accounting-voucher-detail'

const AccountingVoucherDetailAPI = {
  list(query?: AccountingVoucherDetailPageQuery) {
    return request<ApiResponse<AccountingVoucherDetailPageResult>>({
      url: `${API_PATH}/list`,
      method: 'get',
      params: query,
    })
  },

  detail(id: number) {
    return request<ApiResponse<AccountingVoucherDetailTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: 'get',
    })
  },

  create(body: AccountingVoucherDetailForm) {
    return request<ApiResponse<AccountingVoucherDetailTable>>({
      url: `${API_PATH}/create`,
      method: 'post',
      data: body,
    })
  },

  update(id: number, body: AccountingVoucherDetailForm) {
    return request<ApiResponse<AccountingVoucherDetailTable>>({
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

  export(query: AccountingVoucherDetailExportQuery) {
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
    return request<ApiResponse<AccountingVoucherDetailImportResult>>({
      url: `${API_PATH}/import/data`,
      method: 'post',
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

export default AccountingVoucherDetailAPI

export interface AccountingVoucherDetailPageQuery extends PageQuery {
  year?: number
  company_id?: number
  voucher_number?: string
  accounting_subject_ids?: number[]
  cost_center_ids?: number[]
  department_ids?: number[]
  belonging_months?: number[]
  data_source_category?: string[]
  posting_date?: string[]
}

export type AccountingVoucherDetailExportQuery = Omit<
  AccountingVoucherDetailPageQuery,
  'page_no' | 'page_size'
>

export interface AccountingVoucherDetailPageResult extends PageResult<AccountingVoucherDetailTable> {
  amount_sum: number | string
}

export interface AccountingVoucherDetailTable extends BaseType {
  id: number
  year: number
  company_id: number
  company_code?: string | null
  company_name?: string | null
  voucher_number: string
  line_number: string
  accounting_subject_id: number
  accounting_subject_code?: string | null
  accounting_subject_name?: string | null
  cost_center_id?: number | null
  cost_center_code?: string | null
  cost_center_name?: string | null
  belonging_month: number
  posting_date: string
  currency: string
  amount: number | string
  debit_credit_direction: '借' | '贷'
  voucher_text?: string | null
  data_source_category: string
  source_description?: string | null
}

export interface AccountingVoucherDetailForm {
  year?: number
  company_id?: number
  voucher_number?: string
  line_number?: string
  accounting_subject_id?: number
  cost_center_id?: number | null
  belonging_month?: number | null
  posting_date?: string
  currency?: string
  amount?: number
  debit_credit_direction?: '借' | '贷'
  voucher_text?: string | null
  data_source_category?: string
  source_description?: string | null
}

export interface AccountingVoucherDetailImportError {
  row_number: number
  voucher_number?: string | null
  line_number?: string | null
  reason: string
}

export interface AccountingVoucherDetailImportResult {
  total_count: number
  success_count: number
  created_count: number
  updated_count: number
  duplicate_count: number
  failed_count: number
  errors: AccountingVoucherDetailImportError[]
  errors_truncated: boolean
}
