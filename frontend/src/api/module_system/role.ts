import request from "@/utils/request";

import type { MenuTable } from "./menu";
import type { DeptTable } from "./dept";

const API_PATH = "/system/role";

const RoleAPI = {
  listRole(query?: TablePageQuery) {
    return request<ApiResponse<PageResult<RoleTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  detailRole(id: number) {
    return request<ApiResponse<RoleTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  createRole(body: RoleForm) {
    return request<ApiResponse<RoleTable>>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  updateRole(id: number, body: RoleForm) {
    return request<ApiResponse<RoleTable>>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  deleteRole(ids: number[]) {
    return request<ApiResponse<null>>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: ids,
    });
  },

  batchRole(body: BatchType) {
    return request<ApiResponse<null>>({
      url: `${API_PATH}/available/setting`,
      method: "patch",
      data: body,
    });
  },

  setPermission(body: PermissionDataType) {
    return request<ApiResponse<null>>({
      url: `${API_PATH}/permission/setting`,
      method: "patch",
      data: body,
    });
  },

  exportRole(body: RoleExportQuery) {
  return request<Blob>({
    url: `${API_PATH}/export`,
    method: "post",
    data: body,
    responseType: "blob",
  });
}
};

export default RoleAPI;

/**
 * 角色分页查询
 */
export interface TablePageQuery extends PageQuery {
  name?: string;
  status?: string;
  created_time?: string[];
  updated_time?: string[];
}

export interface RoleExportQuery {
  name?: string;
  status?: string;
  created_time?: string[];
  updated_time?: string[];
}

/**
 * 角色
 */
export interface RoleTable extends BaseType {
  id: number;

  name: string;

  order?: number;

  code: string;

  data_scope?: number;

  status?: string;

  description?: string;

  menus?: MenuTable[];

  depts?: DeptTable[];
}

/**
 * 角色表单
 */
export interface RoleForm extends BaseFormType {
  name: string;

  order?: number;

  code: string;

  data_scope?: number;

  status?: string;

  description?: string;
}

/**
 * 权限设置
 */
export interface PermissionDataType {
  data_scope: number;

  role_ids: number[];

  menu_ids: number[];

  dept_ids: number[];
}

/**
 * 权限类型别名
 *
 * 直接复用菜单和部门的数据类型，
 * 避免维护两套完全相同的 interface。
 */
export type PermissionMenuType = MenuTable;

export type PermissionDeptType = DeptTable;
