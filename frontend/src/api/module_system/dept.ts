import request from "@/utils/request";

const API_PATH = "/system/dept";

const DeptAPI = {
  /**
   * 查询部门树
   */
  listDept(query?: DeptPageQuery) {
    return request<ApiResponse<DeptTable[]>>({
      url: `${API_PATH}/tree`,
      method: "get",
      params: query,
    });
  },

  /**
   * 查询部门详情
   */
  detailDept(id: number) {
    return request<ApiResponse<DeptTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  /**
   * 创建部门
   */
  createDept(body: DeptForm) {
    return request<ApiResponse<DeptTable>>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  /**
   * 修改部门
   */
  updateDept(id: number, body: DeptForm) {
    return request<ApiResponse<DeptTable>>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },
  

  /**
   * 删除部门
   */
  deleteDept(ids: number[]) {
    return request<ApiResponse<null>>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: ids,
    });
  },

  /**
   * 批量修改部门状态
   */
  batchDept(body: BatchType) {
    return request<ApiResponse<null>>({
      url: `${API_PATH}/available/setting`,
      method: "patch",
      data: body,
    });
  },
};

export default DeptAPI;

/**
 * 部门查询参数
 */
export interface DeptPageQuery {
  name?: string;

  status?: string;

  created_time?: string[];

  updated_time?: string[];
}


/**
 * 部门树节点
 */

export interface DeptTable extends BaseType {
  /**
   * 数据库主键必须存在
   */
  id: number;

  name?: string;

  order?: number;

  code: string;

  leader?: string;

  phone?: string;

  email?: string;

  parent_id?: number | null;

  parent_name?: string;

  status?: string;

  description?: string;

  children?: DeptTable[];
}

/**
 * 部门表单
 */
export interface DeptForm extends BaseFormType {

  name?: string;

  order?: number;

  code: string;

  leader?: string;

  phone?: string;

  email?: string;

  parent_id?: number | null;

  status?: string;

  description?: string;
}
