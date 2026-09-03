import request from "@/utils/request";

const API_PATH = "/system/menu";

const MenuAPI = {
  /**
   * 查询菜单树
   */
  listMenu(query?: MenuPageQuery) {
    return request<ApiResponse<MenuTable[]>>({
      url: `${API_PATH}/tree`,
      method: "get",
      params: query,
    });
  },

  /**
   * 查询菜单详情
   */
  detailMenu(id: number) {
    return request<ApiResponse<MenuTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  /**
   * 创建菜单
   */
  createMenu(body: MenuForm) {
    return request<ApiResponse<MenuTable>>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  /**
   * 修改菜单
   */
  updateMenu(id: number, body: MenuForm) {
    return request<ApiResponse<MenuTable>>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  /**
   * 删除菜单
   */
  deleteMenu(ids: number[]) {
    return request<ApiResponse<null>>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: ids,
    });
  },

  /**
   * 批量修改菜单状态
   */
  batchMenu(body: BatchType) {
    return request<ApiResponse<null>>({
      url: `${API_PATH}/available/setting`,
      method: "patch",
      data: body,
    });
  },
};

export default MenuAPI;

/**
 * 菜单查询参数
 */
export interface MenuPageQuery {
  name?: string;
  type?: number;
  route_path?: string;
  component_path?: string;
  permission?: string;
  
  status?: string;

  created_time?: string[];

  updated_time?: string[];

  /**
   * PC / APP
   */
  menu_client?: "pc" | "app";
}

/**
 * 菜单树节点
 */
export interface MenuTable extends BaseType {
  /**
   * 数据库主键必须存在
   */
  id: number;

  name?: string;

  type?: number;

  icon?: string;

  order?: number;

  permission?: string;

  route_name?: string;

  route_path?: string;

  component_path?: string;

  redirect?: string;

  parent_id?: number | null;

  parent_name?: string;

  keep_alive?: boolean;

  hidden?: boolean;

  always_show?: boolean;

  title?: string;

  params?: {
    key: string;
    value: string;
  }[];

  affix?: boolean;

  status?: string;

  description?: string;

  children?: MenuTable[];

  client?: "pc" | "app";
}

/**
 * 菜单表单
 */
export interface MenuForm extends BaseFormType {
  name?: string;

  type?: number;

  icon?: string;

  order?: number;

  permission?: string;

  route_name?: string;

  route_path?: string;

  component_path?: string;

  redirect?: string;

  parent_id?: number | null;

  keep_alive?: boolean;

  hidden?: boolean;

  always_show?: boolean;

  title?: string;

  params?: KeyValue[];

  affix?: boolean;

  client?: "pc" | "app";
}

/**
 * Key / Value
 */
export interface KeyValue {
  key: string;
  value: string;
}
