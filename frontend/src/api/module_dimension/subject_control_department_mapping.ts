import request from '@/utils/request'

const API_PATH = '/dimension/subject-control-department-mapping'

const SubjectControlDepartmentMappingAPI = {
  options() {
    return request<ApiResponse<SubjectControlDepartmentMappingOptions>>({
      url: `${API_PATH}/options`,
      method: 'get',
    })
  },

  list(query?: SubjectControlDepartmentMappingPageQuery) {
    return request<ApiResponse<PageResult<SubjectControlDepartmentMappingTable>>>({
      url: `${API_PATH}/list`,
      method: 'get',
      params: query,
    })
  },

  detail(id: number) {
    return request<ApiResponse<SubjectControlDepartmentMappingTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: 'get',
    })
  },

  create(body: SubjectControlDepartmentMappingForm) {
    return request<ApiResponse<SubjectControlDepartmentMappingTable>>({
      url: `${API_PATH}/create`,
      method: 'post',
      data: body,
    })
  },

  update(id: number, body: SubjectControlDepartmentMappingForm) {
    return request<ApiResponse<SubjectControlDepartmentMappingTable>>({
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
}

export default SubjectControlDepartmentMappingAPI

export interface SubjectControlDepartmentMappingPageQuery extends PageQuery {
  accounting_subject_id?: number
  dept_id?: number
  control_department?: string
  control_person?: string
  status?: string
}

export interface SubjectControlDepartmentMappingTable extends BaseType {
  id: number
  accounting_subject_id: number
  dept_id: number
  control_department: string
  control_person: string
  accounting_subject_code?: string | null
  accounting_subject_name?: string | null
  dept_code?: string | null
  dept_name?: string | null
  status?: string
  description?: string
  created_time?: string
  updated_time?: string
}

export interface SubjectControlDepartmentMappingOption {
  id: number
  code: string
  name: string
}

export interface SubjectControlDepartmentMappingOptions {
  accounting_subjects: SubjectControlDepartmentMappingOption[]
  departments: SubjectControlDepartmentMappingOption[]
}

export interface SubjectControlDepartmentMappingForm {
  accounting_subject_id?: number
  dept_id?: number
  control_department?: string
  control_person?: string
  status?: string
  description?: string | null
}
