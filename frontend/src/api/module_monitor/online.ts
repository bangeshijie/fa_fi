import request from '@/utils/request'

const API_PATH = '/monitor/online'

export interface OnlinePageQuery extends PageQuery {
  name?: string
  ipaddr?: string
  login_location?: string
}

export interface OnlineUser {
  name: string
  session_id: string
  user_id: number
  is_super_admin?: boolean
  user_name: string
  avatar?: string | null
  ipaddr?: string
  login_location?: string
  os?: string
  browser?: string
  login_time?: string
  login_type?: string
}

const OnlineAPI = {
  listOnline(query: OnlinePageQuery) {
    return request<ApiResponse<PageResult<OnlineUser>>>({
      url: `${API_PATH}/list`,
      method: 'get',
      params: query,
    })
  },

  deleteOnline(sessionId: string) {
    return request<ApiResponse<null>>({
      url: `${API_PATH}/delete`,
      method: 'delete',
      data: sessionId,
    })
  },

  clearOnline() {
    return request<ApiResponse<null>>({
      url: `${API_PATH}/clear`,
      method: 'delete',
    })
  },
}

export default OnlineAPI
