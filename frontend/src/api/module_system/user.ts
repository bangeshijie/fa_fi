import type { AxiosResponse } from "axios";

import request, { type ExtendedRequestConfig } from "@/utils/request";
import type{ MenuTable, MenuForm } from "@/api/module_system/menu";

const API_PATH = "/system/user";

export const UserAPI = {
  getCurrentUserInfo() {
    return request<ApiResponse<UserInfo>>({
      url: `${API_PATH}/current/info`,
      method: "get",
    });
  },

  uploadCurrentUserAvatar(body: FormData) {
    return request<ApiResponse<UploadFilePath>>({
      url: `/common/file/upload?upload_type=avatar`,
      method: "post",
      data: body,
    });
  },

  updateCurrentUserInfo(body: InfoFormState) {
    return request<ApiResponse<UserInfo>>({
      url: `${API_PATH}/current/info/update`,
      method: "put",
      data: body,
    });
  },

  changeCurrentUserPassword(body: PasswordFormState) {
    return request<ApiResponse>({
      url: `${API_PATH}/current/password/change`,
      method: "put",
      data: body,
    });
  },

  resetUserPassword(body: ResetPasswordForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/reset/password`,
      method: "put",
      data: body,
    });
  },

  registerUser(body: RegisterForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/register`,
      method: "post",
      data: body,
    });
  },

  forgetPassword(body: ForgetPasswordForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/forget/password`,
      method: "post",
      data: body,
    });
  },

  listUser(query: UserPageQuery) {
    return request<ApiResponse<PageResult<UserInfo>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  detailUser(query: number) {
    return request<ApiResponse<UserInfo>>({
      url: `${API_PATH}/detail/${query}`,
      method: "get",
    });
  },

  createUser(body: UserForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  updateUser(id: number, body: UserForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  deleteUser(body: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: body,
    });
  },

  batchUser(body: BatchType) {
    return request<ApiResponse>({
      url: `${API_PATH}/available/setting`,
      method: "patch",
      data: body,
    });
  },

  exportUser(body: UserPageQuery) {
    return request<Blob>({
      url: `${API_PATH}/export`,
      method: "post",
      params: body,
      responseType: "blob",
    });
  },

  downloadTemplateUser() {
    return request<ApiResponse>({
      url: `${API_PATH}/import/template`,
      method: "post",
      responseType: "blob",
    });
  },

  importUser(body: FormData): Promise<AxiosResponse<ApiResponse<UserImportResult>>> {
    return request<ApiResponse<UserImportResult>>({
      url: `${API_PATH}/import/data`,
      method: "post",
      data: body,
      headers: {
        "Content-Type": "multipart/form-data",
      },
      showSuccessMessage: false,
    } as ExtendedRequestConfig);
  },
};

export default UserAPI;

export interface UserImportError {
  row_number: number;
  username?: string | null;
  reason: string;
}

export interface UserImportResult {
  total_count: number;
  success_count: number;
  created_count: number;
  updated_count: number;
  duplicate_count: number;
  failed_count: number;
  errors: UserImportError[];
  errors_truncated: boolean;
}

export interface ForgetPasswordForm {
  username: string;
  new_password: string;
  mobile?: string;
  confirmPassword: string;
}

export interface RegisterForm {
  username: string;
  password: string;
  confirmPassword: string;
}

export interface UserPageQuery extends PageQuery {
  username?: string;
  name?: string;
  mobile?: string;
  email?: string;
  dept_id?: number;
  status?: string;
  created_time?: string[];
  created_id?: number;
  updated_id?: number;
}

export interface searchSelectDataType {
  name?: string;
  status?: string;
}

export interface UserInfo extends BaseType {
  id: number;
  username?: string;
  name?: string;
  avatar?: string;
  email?: string;
  mobile?: string;
  gender?: string;
  password?: string;
  menus?: MenuTable[];
  dept?: deptTreeType;
  dept_id?: deptTreeType["id"];
  roles?: roleSelectorType[];
  role_ids?: roleSelectorType["id"][];
  positions?: positionSelectorType[];
  position_names?: positionSelectorType["name"][];
  position_ids?: positionSelectorType["id"][];
  is_superuser?: boolean;
  last_login?: string;
  created_by?: CommonType;
  updated_by?: CommonType;
  deleted_by?: CommonType;
  gitee_login?: string;
  github_login?: string;
  wx_login?: string;
  qq_login?: string;
  description?: string;
}

export interface deptTreeType {
  id?: number;
  name?: string;
  parent_id?: number;
  children?: deptTreeType[];
}

export interface roleSelectorType {
  id: number;
  name: string;
  code?: string;
  status?: string;
  description?: string;
  menus?: MenuForm[];
}

export interface positionSelectorType {
  id: number;
  name: string;
  status?: string;
  description?: string;
}

export interface InfoFormState {
  id?: number;
  name?: string;
  gender?: string;
  mobile?: string;
  email?: string;
  username?: string;
  dept?: deptTreeType;
  positions?: positionSelectorType[];
  roles?: roleSelectorType[];
  avatar?: string;
  created_time?: string;
  updated_time?: string;
}

export interface PasswordFormState {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export interface ResetPasswordForm {
  id: number;
  password: string;
}

export interface UserForm extends BaseFormType {
  username?: string;
  name?: string;
  dept_id?: number;
  role_ids?: number[];
  position_ids?: number[];
  position_names?: string[];
  password?: string;
  gender?: string;
  email?: string;
  mobile?: string;
  is_superuser?: boolean;
}

export interface CurrentUserFormState {
  name?: string;
  gender?: string;
  mobile?: string;
  email?: string;
  avatar?: string;
}
