declare global {
  /**
   * 系统设置
   */
  // pass

  /**
   * 下拉选项数据类型
   */
  interface OptionType {
    /** 值 */
    value: string | number;
    /** 文本 */
    label: string;
    /** 子列表  */
    children?: OptionType[];
  }

  /**
   * 导入结果
   */
  interface ExcelResult {
    /** 状态码 */
    code: string;
    /** 无效数据条数 */
    invalidCount: number;
    /** 有效数据条数 */
    validCount: number;
    /** 错误信息 */
    messageList: Array<string>;
  }

  /**
   * 基础响应结构
   */
  interface ApiResponse<T = any> {
    code: number;
    data: T;
    msg: string;
    status_code: number;
    success: boolean;
  }



  /**
   * 分页查询参数
   */
  interface PageQuery {
    page_no: number;
    page_size: number;
  }



  /**
   * 分页响应对象（列表接口 `data` 统一为该结构）
   * 前端 `useTable` 仅通过 `@utils/table` 的 `defaultResponseAdapter` 解析该形状（及 ApiResponse 包装）
   */
  interface PageResult<T = any> {
    items: T[];
    total: number;
    page_no: number;
    page_size: number;
    has_next: boolean;
  }


  /**
   * 创建人
   */
  interface CommonType {
    id?: number;
    name?: string;
  }



  /**
   * 基础类型
   */
  interface BaseType {
    index?: number;
    id?: number;
    uuid?: string;
    status?: string;
    description?: string;
    created_time?: string;
    updated_time?: string;
    deleted_time?: string;
    deleted_id?: number;
  }


  /**
   * 基础表单类型
   */
  interface BaseFormType {
    id?: number;
    status?: string;
    description?: string;
    remark?: string;
    order?: number;
  }

  /**
   * 批量操作类型
   */
  interface BatchType {
    ids: number[];
    status: string;
  }

  /**
   * 上传文件路径
   */
  interface UploadFilePath {
    file_path: string;
    file_name: string;
    origin_name: string;
    file_url: string;
  }

  /**
   * 通用搜索参数
   */
  type CommonSearchParams = Pick<PageQuery, "page_no" | "page_size">;

  /**
   * 通用启用状态
   */
  type EnableStatus = "0" | "1";


  /**
   * 登录参数
   */
  interface LoginParams {
    username: string;
    password: string;
    captcha_key?: string;
    captcha?: string;
    remember?: boolean;
    login_type?: string;
  }

  /**
   * 登录响应
   */
  interface LoginResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
  }

  /**
   * 用户信息
   */
  interface UserInfo {
    user_id: number;
    username: string;
    nickname?: string;
    email?: string;
    avatar?: string;
    phone?: string;
    roles?: RoleInfo[];
    permissions?: string[];
    menus?: MenuTable[];
    created_at?: string;
    updated_at?: string;
  }

  /**
   * 角色信息
   */
  interface RoleInfo {
    id?: number;
    name?: string;
    code?: string;
    menus?: any[];
  }

  /**
   * 验证码信息
   */
  interface CaptchaInfo {
    enable: boolean;
    key: string;
    img_base: string;
  }

  /**
   * 用户列表
   */
  type UserList = PageResult<UserListItem>;

  /**
   * 用户列表项
   */
  interface UserListItem {
    id: number;
    avatar: string;
    status: string;
    userName: string;
    userGender: string;
    nickName: string;
    userPhone: string;
    userEmail: string;
    userRoles: string[];
    createBy: string;
    createTime: string;
    updateBy: string;
    updateTime: string;
  }

  /**
   * 用户搜索参数
   */
  type UserSearchParams = Partial<
    Pick<UserListItem, "id" | "userName" | "userGender" | "userPhone" | "userEmail" | "status"> &
      CommonSearchParams
  >;

  /**
   * 角色列表
   */
  type RoleList = PaginatedResponse<RoleListItem>;

  /**
   * 角色列表项
   */
  interface RoleListItem {
    roleId: number;
    roleName: string;
    roleCode: string;
    description: string;
    enabled: boolean;
    createTime: string;
  }

  /**
   * 角色搜索参数
   */
  type RoleSearchParams = Partial<
    Pick<RoleListItem, "roleId" | "roleName" | "roleCode" | "description" | "enabled"> &
      CommonSearchParams & {
        startTime: string | null;
        endTime: string | null;
      }
  >;
}

export {};
