import request from '@/utils/request'

const API_PATH = '/dimension/company'

const CompanyAPI = {
  listCompany(query?: CompanyPageQuery) {
    return request<ApiResponse<PageResult<CompanyTable>>>({
      url: `${API_PATH}/list`,
      method: 'get',
      params: query,
    })
  },

  listCompanyOptions() {
    return request<ApiResponse<CompanyOption[]>>({
      url: `${API_PATH}/options`,
      method: 'get',
    })
  },

  detailCompany(id: number) {
    return request<ApiResponse<CompanyTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: 'get',
    })
  },

  createCompany(body: CompanyForm) {
    return request<ApiResponse<CompanyTable>>({
      url: `${API_PATH}/create`,
      method: 'post',
      data: body,
    })
  },

  updateCompany(id: number, body: CompanyForm) {
    return request<ApiResponse<CompanyTable>>({
      url: `${API_PATH}/update/${id}`,
      method: 'put',
      data: body,
    })
  },

  deleteCompany(ids: number[]) {
    return request<ApiResponse<null>>({
      url: `${API_PATH}/delete`,
      method: 'delete',
      data: ids,
    })
  },

  batchCompany(body: BatchType) {
    return request<ApiResponse<null>>({
      url: `${API_PATH}/available/setting`,
      method: 'patch',
      data: body,
    })
  },

  exportCompany(body: CompanyExportQuery) {
    return request<Blob>({
      url: `${API_PATH}/export`,
      method: 'post',
      data: body,
      responseType: 'blob',
    })
  },
}

export default CompanyAPI

export interface CompanyPageQuery extends PageQuery {
  code?: string
  name?: string
  address?: string
  phone?: string
  business_license_no?: string
  leader?: string
  status?: string
  created_time?: string[]
  updated_time?: string[]
}

export type CompanyExportQuery = Omit<CompanyPageQuery, 'page_no' | 'page_size'>

export interface CompanyTable extends BaseType {
  id: number
  code: string
  name: string
  holding_company_id?: number | null
  holding_company_code?: string | null
  holding_company_name?: string | null
  address?: string | null
  phone?: string | null
  business_license_no?: string | null
  leader?: string | null
  holding_ratio?: number | null
  registered_capital?: number | null
  status?: string
  description?: string
  created_time?: string
  updated_time?: string
}

export interface CompanyOption {
  id: number
  code: string
  name: string
}

export interface CompanyForm extends BaseFormType {
  code?: string
  name?: string
  holding_company_id?: number | null
  address?: string | null
  phone?: string | null
  business_license_no?: string | null
  leader?: string | null
  holding_ratio?: number | null
  registered_capital?: number | null
  status?: string
  description?: string
}
