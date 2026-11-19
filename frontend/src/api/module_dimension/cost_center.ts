import request from '@/utils/request'

const API_PATH = '/dimension/cost-center'

const CostCenterAPI = {
  listOptions() {
    return request<ApiResponse<CostCenterOption[]>>({
      url: `${API_PATH}/options`,
      method: 'get',
    })
  },

  list(query?: CostCenterPageQuery) {
    return request<ApiResponse<PageResult<CostCenterTable>>>({
      url: `${API_PATH}/list`,
      method: 'get',
      params: query,
    })
  },

  listCompanyOptions() {
    return request<ApiResponse<CompanyOption[]>>({
      url: '/dimension/company/options',
      method: 'get',
    })
  },

  listDepartmentOptions() {
    return request<ApiResponse<DepartmentOption[]>>({
      url: `${API_PATH}/department-options`,
      method: 'get',
    })
  },

  detail(id: number) {
    return request<ApiResponse<CostCenterTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: 'get',
    })
  },

  create(body: CostCenterForm) {
    return request<ApiResponse<CostCenterTable>>({
      url: `${API_PATH}/create`,
      method: 'post',
      data: body,
    })
  },

  update(id: number, body: CostCenterForm) {
    return request<ApiResponse<CostCenterTable>>({
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

  export(query: CostCenterExportQuery) {
    return request<Blob>({
      url: `${API_PATH}/export`,
      method: 'post',
      data: query,
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
    return request<ApiResponse<CostCenterImportResult>>({
      url: `${API_PATH}/import/data`,
      method: 'post',
      data: formData,
    })
  },
}

export default CostCenterAPI

export interface CostCenterPageQuery extends PageQuery {
  code?: string
  name?: string
  company_id?: number
  function_scope?: string
  dept_id?: number
  leader?: string
  status?: string
}

export type CostCenterExportQuery = Omit<CostCenterPageQuery, 'page_no' | 'page_size'>

export interface CostCenterTable extends BaseType {
  id: number
  code: string
  name: string
  company_id: number
  company_code?: string | null
  company_name?: string | null
  function_scope: string
  dept_id: number
  dept_code?: string | null
  dept_name?: string | null
  leader?: string | null
  enable_time?: string | null
  status?: string
  description?: string
  created_time?: string
  updated_time?: string
}

export interface CostCenterForm {
  code?: string
  name?: string
  company_id?: number
  function_scope?: string
  dept_id?: number
  leader?: string | null
  enable_time?: string
  status?: string
  description?: string | null
}

export interface CompanyOption {
  id: number
  code: string
  name: string
}

export interface DepartmentOption {
  id: number
  code: string
  name: string
  parent_id?: number | null
}

export interface CostCenterOption {
  id: number
  code: string
  name: string
}

export interface CostCenterImportError {
  row_number: number
  code?: string | null
  reason: string
}

export interface CostCenterImportResult {
  total_count: number
  success_count: number
  created_count: number
  updated_count: number
  duplicate_count: number
  failed_count: number
  errors: CostCenterImportError[]
  errors_truncated: boolean
}
