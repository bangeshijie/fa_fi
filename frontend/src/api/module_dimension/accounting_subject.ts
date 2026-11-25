import request from '@/utils/request'

const API_PATH = '/dimension/accounting-subject'

const AccountingSubjectAPI = {
  options() {
    return request<ApiResponse<AccountingSubjectOption[]>>({
      url: `${API_PATH}/options`,
      method: 'get',
    })
  },

  categoryOptions() {
    return request<ApiResponse<AccountingSubjectCategoryOption[]>>({
      url: `${API_PATH}/category-options`,
      method: 'get',
    })
  },

  list(query?: AccountingSubjectPageQuery) {
    return request<ApiResponse<PageResult<AccountingSubjectTable>>>(
      {
        url: `${API_PATH}/list`,
        method: 'get',
        params: query,
      },
    )
  },

  detail(id: number) {
    return request<ApiResponse<AccountingSubjectTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: 'get',
    })
  },

  create(body: AccountingSubjectForm) {
    return request<ApiResponse<AccountingSubjectTable>>({
      url: `${API_PATH}/create`,
      method: 'post',
      data: body,
    })
  },

  update(id: number, body: AccountingSubjectForm) {
    return request<ApiResponse<AccountingSubjectTable>>({
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

  batchStatus(body: BatchType) {
    return request<ApiResponse<null>>({
      url: `${API_PATH}/available/setting`,
      method: 'patch',
      data: body,
    })
  },

  export(query: AccountingSubjectExportQuery) {
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
    return request<ApiResponse<AccountingSubjectImportResult>>({
      url: `${API_PATH}/import/data`,
      method: 'post',
      data: formData,
    })
  },
}

export default AccountingSubjectAPI

export interface AccountingSubjectPageQuery extends PageQuery {
  code?: string
  name?: string
  balance_direction?: string
  accounting_statement_subject?: string
  management_category_paths?: string[]
  status?: string
}

export type AccountingSubjectExportQuery = Omit<
  AccountingSubjectPageQuery,
  'page_no' | 'page_size'
>

export interface AccountingSubjectTable extends BaseType {
  id: number
  code: string
  name: string
  balance_direction: string
  accounting_statement_subject?: string | null
  management_category_level3?: string | null
  management_category_level1?: string | null
  management_category_level2?: string | null
  status?: string
  description?: string
  created_time?: string
  updated_time?: string
}

export interface AccountingSubjectOption {
  id: number
  code: string
  name: string
}

export interface AccountingSubjectCategoryOption {
  value: string
  label: string
  children?: AccountingSubjectCategoryOption[]
}

export interface AccountingSubjectForm {
  code?: string
  name?: string
  balance_direction?: string
  accounting_statement_subject?: string | null
  management_category_level3?: string | null
  management_category_level1?: string | null
  management_category_level2?: string | null
  status?: string
  description?: string | null
}

export interface AccountingSubjectImportError {
  row_number: number
  code?: string | null
  reason: string
}

export interface AccountingSubjectImportResult {
  total_count: number
  success_count: number
  created_count: number
  updated_count: number
  duplicate_count: number
  failed_count: number
  errors: AccountingSubjectImportError[]
  errors_truncated: boolean
}
