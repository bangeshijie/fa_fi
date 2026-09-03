import request from "@/utils/request";

const API_PATH = "/system/log";

const LogAPI = {
  listLog(query: LogPageQuery) {
    return request<ApiResponse<PageResult<LogTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  detailLog(query: number) {
    return request<ApiResponse<LogTable>>({
      url: `${API_PATH}/detail/${query}`,
      method: "get",
    });
  },

  deleteLog(body: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: body,
    });
  },

  exportLog(body: LogPageQuery) {
    return request<Blob>({
      url: `${API_PATH}/export`,
      method: "post",
      // 后端导出接口通过 Depends(OperationLogQueryParam) 接收查询参数。
      params: body,
      responseType: "blob",
    });
  },
};

export default LogAPI;

export interface LogPageQuery extends PageQuery {
  type?: number;
  request_path?: string;
  request_method?: string;
  request_ip?: string;
  response_code?: number;
  description?: string;
  status?: string;
  created_time?: string[];
  updated_time?: string[];
  created_id?: number;
  updated_id?: number;
}

export interface LogTable extends BaseType {
  type?: number; // 1 登录日志 2 操作日志
  request_path?: string;
  request_method?: string;
  request_ip?: string;
  login_location?: string;
  request_browser?: string;
  request_os?: string;
  response_code?: number;
  request_payload?: string;
  response_json?: string;
  process_time?: string;
  status?: string;
  description?: string;
  created_id?: number;
  updated_id?: number;
  created_by?: CommonType;
  updated_by?: CommonType;
  deleted_by?: CommonType;
}
