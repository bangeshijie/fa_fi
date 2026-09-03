/**
 * HTTP
 *
 * Axios 实例
 * Token 注入
 * Token 刷新
 * 401 并发控制
 * 错误处理
 */

import axios, {
  type AxiosError,
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios";

import qs from "qs";
import { ElMessage } from "element-plus";

import { ResultEnum } from "@/enums/api/result.enum";
import {
  Auth,
  redirectToLogin,
} from "@/utils/auth";

// ============================================================
// 常量
// ============================================================

/**
 * 不携带 Token
 */
export const NO_AUTH_FLAG = "no-auth";

// ============================================================
// Axios Config
// ============================================================

export interface ExtendedRequestConfig
  extends AxiosRequestConfig {
  /**
   * 是否跳过 Access Token
   */
  skipAuth?: boolean;

  /**
   * 是否显示成功消息
   */
  showSuccessMessage?: boolean;

  /**
   * 是否显示错误消息
   */
  showErrorMessage?: boolean;

  /**
   * 是否已经重试过
   */
  _retry?: boolean;
}

// ============================================================
// HTTP 状态码
// ============================================================

export const ApiStatus = {
  success: 200,
  error: 400,
  unauthorized: 401,
  forbidden: 403,
  notFound: 404,
  methodNotAllowed: 405,
  requestTimeout: 408,
  internalServerError: 500,
  notImplemented: 501,
  badGateway: 502,
  serviceUnavailable: 503,
  gatewayTimeout: 504,
  httpVersionNotSupported: 505,
} as const;

export type ApiStatus =
  (typeof ApiStatus)[keyof typeof ApiStatus];

// ============================================================
// HttpError
// ============================================================

export interface ErrorLogData {
  code: number;
  message: string;
  data?: unknown;
  timestamp: string;
  url?: string;
  method?: string;
  stack?: string;
}

export class HttpError extends Error {
  public readonly code: number;
  public readonly data?: unknown;
  public readonly timestamp: string;
  public readonly url?: string;
  public readonly method?: string;

  constructor(
    message: string,
    code: number,
    options?: {
      data?: unknown;
      url?: string;
      method?: string;
    }
  ) {
    super(message);

    this.name = "HttpError";
    this.code = code;
    this.data = options?.data;
    this.timestamp = new Date().toISOString();
    this.url = options?.url;
    this.method = options?.method;

    Object.setPrototypeOf(
      this,
      HttpError.prototype
    );
  }

  public toLogData(): ErrorLogData {
    return {
      code: this.code,
      message: this.message,
      data: this.data,
      timestamp: this.timestamp,
      url: this.url,
      method: this.method,
      stack: this.stack,
    };
  }
}

export const isHttpError = (
  error: unknown
): error is HttpError => {
  return error instanceof HttpError;
};

// ============================================================
// 错误消息
// ============================================================

const getErrorMessage = (
  status: number
): string => {
  const errorMap: Record<
    number,
    string
  > = {
    [ApiStatus.unauthorized]:
      "httpMsg.unauthorized",

    [ApiStatus.forbidden]:
      "httpMsg.forbidden",

    [ApiStatus.notFound]:
      "httpMsg.notFound",

    [ApiStatus.methodNotAllowed]:
      "httpMsg.methodNotAllowed",

    [ApiStatus.requestTimeout]:
      "httpMsg.requestTimeout",

    [ApiStatus.internalServerError]:
      "httpMsg.internalServerError",

    [ApiStatus.badGateway]:
      "httpMsg.badGateway",

    [ApiStatus.serviceUnavailable]:
      "httpMsg.serviceUnavailable",

    [ApiStatus.gatewayTimeout]:
      "httpMsg.gatewayTimeout",
  };

  return (
    errorMap[status] ||
    "httpMsg.internalServerError"
  );
};

// ============================================================
// Axios Error
// ============================================================

export function handleError(
  error: AxiosError<ApiResponse>
): never {
  if (error.code === "ERR_CANCELED") {
    throw new HttpError(
      "httpMsg.requestCancelled",
      ApiStatus.error
    );
  }

  const statusCode =
    error.response?.status;

  const requestConfig =
    error.config;

  if (!error.response) {
    throw new HttpError(
      "httpMsg.networkError",
      ApiStatus.error,
      {
        url: requestConfig?.url,
        method:
          requestConfig?.method?.toUpperCase(),
      }
    );
  }

  const message =
    getErrorMessage(
      statusCode || ApiStatus.error
    );

  throw new HttpError(
    message,
    statusCode || ApiStatus.error,
    {
      data: error.response.data,
      url: requestConfig?.url,
      method:
        requestConfig?.method?.toUpperCase(),
    }
  );
}

// ============================================================
// 消息
// ============================================================

export function showError(
  error: HttpError,
  showMessage = true
): void {
  if (showMessage) {
    ElMessage.error(error.message);
  }

  console.error(
    "[HTTP Error]",
    error.toLogData()
  );
}

export function showSuccess(
  message: string,
  showMessage = true
): void {
  if (showMessage) {
    ElMessage.success(message);
  }
}

// ============================================================
// Token 刷新状态
// ============================================================

let isRefreshing = false;

/**
 * 等待 Token 刷新的请求。
 */
let pendingRequests: Array<{
  config: InternalAxiosRequestConfig;
  resolve: (
    value: AxiosResponse
  ) => void;
  reject: (
    reason?: unknown
  ) => void;
}> = [];

/**
 * Token 刷新成功。
 */
function onRefreshed(
  newAccessToken: string
): void {
  const requests =
    pendingRequests;

  pendingRequests = [];

  requests.forEach(async ({
    config,
    resolve,
    reject,
  }) => {
    try {
      config.headers.Authorization =
        `Bearer ${newAccessToken}`;

      const response = await request(config);
      resolve(response);
    } catch (error) {
      reject(error);
    }
  });
 
}

/**
 * Token 刷新失败。
 */
function onRefreshFailed(
  reason: unknown
): void {
  const requests =
    pendingRequests;

  pendingRequests = [];

  requests.forEach(
    ({ reject }) => {
      reject(reason);
    }
  );
}

// ============================================================
// Axios 实例
// ============================================================

export const request: AxiosInstance =
  axios.create({
    baseURL:
      import.meta.env.VITE_APP_BASE_API,

    timeout:
      Number(
        import.meta.env.VITE_TIMEOUT
      ) || 15000,

    headers: {
      "Content-Type":
        "application/json;charset=utf-8",
    },

    paramsSerializer: (params) =>
      qs.stringify(params, {
        indices: false,
      }),
  });

// ============================================================
// Request Interceptor
// ============================================================

request.interceptors.request.use(
  (
    config: InternalAxiosRequestConfig
  ) => {
    const extendedConfig =
      config as InternalAxiosRequestConfig &
        ExtendedRequestConfig;

    // Axios 的默认 JSON Content-Type 会阻止后端按 multipart 解析 FormData。
    // 删除它后由浏览器自动补上 boundary。
    if (typeof FormData !== 'undefined' && config.data instanceof FormData) {
      delete config.headers['Content-Type'];
    }

    const accessToken =
      Auth.getAccessToken();

    const authorization =
      config.headers.Authorization;

    // ==========================================================
    // 1. 明确跳过认证
    // ==========================================================

    if (
      extendedConfig.skipAuth ||
      authorization === NO_AUTH_FLAG
    ) {
      delete config.headers.Authorization;

      return config;
    }

    // ==========================================================
    // 2. 自动注入 Access Token
    // ==========================================================

    if (
      !authorization &&
      accessToken
    ) {
      config.headers.Authorization =
        `Bearer ${accessToken}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// ============================================================
// Response Interceptor
// ============================================================

request.interceptors.response.use(
  (
    response: AxiosResponse<ApiResponse>
  ) => {
    // ==========================================================
    // Blob 直接返回
    // ==========================================================

    if (
      response.config.responseType ===
      "blob"
    ) {
      return response;
    }

    const data =
      response.data;

    // ==========================================================
    // 业务错误
    // ==========================================================

    if (
      data.code !==
      ResultEnum.SUCCESS
    ) {
      const message =
        data.msg ||
        "请求失败";

      ElMessage.error(message);

      return Promise.reject(
        new HttpError(
          message,
          data.code,
          {
            data,
            url:
              response.config.url,
            method:
              response.config.method?.toUpperCase(),
          }
        )
      );
    }

    // ==========================================================
    // 成功消息
    // ==========================================================

    const config =
      response.config as ExtendedRequestConfig;

    if (
      config.showSuccessMessage !==
        false &&
      config.method?.toUpperCase() !==
        "GET" &&
      !config.url?.includes(
        "/system/auth/login"
      ) &&
      !config.url?.includes(
        "/system/auth/logout"
      ) &&
      !config.url?.includes(
        "/system/auth/token/refresh"
      )
    ) {
      ElMessage.success(
        data.msg
      );
    }

    return response;
  },

  async (
    error: AxiosError<ApiResponse>
  ) => {
    // ==========================================================
    // 1. 没有 response
    // ==========================================================

    if (!error.response) {
      let errorMessage =
        "网络连接异常";

      if (
        error.message?.includes(
          "ECONNREFUSED"
        )
      ) {
        errorMessage =
          "服务器连接失败，请检查后端服务是否正常运行";
      } else if (
        error.message?.includes(
          "timeout"
        )
      ) {
        errorMessage =
          "请求超时，请稍后重试";
      } else if (
        error.message?.includes(
          "Network Error"
        )
      ) {
        errorMessage =
          "网络连接错误，请检查您的网络设置";
      }

      ElMessage.error(
        errorMessage
      );

      return Promise.reject(
        new Error(errorMessage)
      );
    }

    const response =
      error.response;

    const data =
      response.data;

    const status =
      response.status;

    const config =
      error.config as
        | (InternalAxiosRequestConfig &
            ExtendedRequestConfig)
        | undefined;

    // ==========================================================
    // 2. Blob 错误
    // ==========================================================

    if (
      response.config.responseType ===
        "blob" &&
      response.data instanceof Blob
    ) {
      try {
        const text =
          await new Response(
            response.data
          ).text();

        const jsonData =
          JSON.parse(
            text
          ) as ApiResponse;

        const message =
          jsonData.msg ||
          "请求错误";

        ElMessage.error(
          message
        );

        return Promise.reject(
          new HttpError(
            message,
            jsonData.code ||
              status,
            {
              data: jsonData,
              url:
                response.config.url,
              method:
                response.config.method?.toUpperCase(),
            }
          )
        );
      } catch {
        ElMessage.error(
          "数据解析失败"
        );

        return Promise.reject(
          new Error(
            "数据解析失败"
          )
        );
      }
    }

    // ==========================================================
    // 3. 401 Token 刷新
    //
    // 非常重要：
    //
    // 不再判断：
    //
    // status === 401 && !hasApiCode
    //
    // 因为你的后端会：
    //
    // HTTP 401
    // code 10401
    //
    // 两者同时存在。
    // ==========================================================

    if (
      status ===
      ApiStatus.unauthorized
    ) {
      // ========================================================
      // Refresh / Logout 自己 401
      //
      // 不能再次刷新，否则死循环。
      // ========================================================

      const url =
        config?.url || "";

      const isRefreshRequest =
        url.includes(
          "/system/auth/token/refresh"
        );

      const isLogoutRequest =
        url.includes(
          "/system/auth/logout"
        );

      if (
        isRefreshRequest ||
        isLogoutRequest
      ) {
        const message =
          data?.msg ||
          "登录状态已失效，请重新登录";

        await redirectToLogin(
          message
        );

        return Promise.reject(
          new HttpError(
            message,
            ApiStatus.unauthorized,
            {
              data,
              url,
              method:
                config?.method?.toUpperCase(),
            }
          )
        );
      }

      // ========================================================
      // 当前请求不存在
      // ========================================================

      if (!config) {
        await redirectToLogin(
          "登录状态已失效，请重新登录"
        );

        return Promise.reject(
          new HttpError(
            "Unauthorized",
            ApiStatus.unauthorized
          )
        );
      }

      // ========================================================
      // 防止同一个请求无限重试
      // ========================================================

      if (config._retry) {
        await redirectToLogin(
          "登录状态已失效，请重新登录"
        );

        return Promise.reject(
          new HttpError(
            "Token refresh retry failed",
            ApiStatus.unauthorized
          )
        );
      }

      config._retry = true;

      // ========================================================
      // 已经有人刷新 Token
      //
      // 当前请求进入等待队列。
      // ========================================================

      if (isRefreshing) {
        return new Promise(
          (
            resolve,
            reject
          ) => {
            pendingRequests.push({
              config,
              resolve,
              reject,
            });
          }
        );
      }

      // ========================================================
      // 当前请求负责刷新 Token
      // ========================================================

      isRefreshing = true;

      try {
        const refreshToken =
          Auth.getRefreshToken();

        // ------------------------------------------------------
        // 没有 Refresh Token
        // ------------------------------------------------------

        if (!refreshToken) {
          throw new Error(
            "没有有效的刷新令牌"
          );
        }

        // ------------------------------------------------------
        // 直接使用 request.post
        //
        // 注意：
        // skipAuth=true
        //
        // 不携带旧 Access Token。
        // ------------------------------------------------------

        const refreshResponse =
          await request.post<
            ApiResponse<{
              access_token: string;
              refresh_token: string;
              token_type: string;
              expires_in: number;
            }>
          >(
            "/system/auth/token/refresh",
            {
              refresh_token:
                refreshToken,
            },
            {
              skipAuth: true,
            } as ExtendedRequestConfig
          );

        const tokenData =
          refreshResponse.data.data;

        const newAccessToken =
          tokenData?.access_token;

        const newRefreshToken =
          tokenData?.refresh_token;

        if (
          !newAccessToken ||
          !newRefreshToken
        ) {
          throw new Error(
            "刷新 Token 响应数据异常"
          );
        }

        // ------------------------------------------------------
        // 保存新的两个 Token
        // ------------------------------------------------------

        Auth.setTokens(
          newAccessToken,
          newRefreshToken,
          Auth.getRememberMe()
        );

        // ------------------------------------------------------
        // 刷新完成
        // ------------------------------------------------------

        isRefreshing = false;

        // ------------------------------------------------------
        // 重放等待请求
        // ------------------------------------------------------

        onRefreshed(
          newAccessToken
        );

        // ------------------------------------------------------
        // 重放当前请求
        // ------------------------------------------------------

        config.headers.Authorization =
          `Bearer ${newAccessToken}`;

        return request(
          config
        );
      } catch (refreshError) {
        // ======================================================
        // Refresh 失败
        // ======================================================

        isRefreshing = false;

        onRefreshFailed(
          refreshError
        );

        const message =
          refreshError instanceof Error
            ? refreshError.message
            : data?.msg ||
              "登录已失效，请重新登录";

        await redirectToLogin(
          message
        );

        return Promise.reject(
          new HttpError(
            message,
            ApiStatus.unauthorized,
            {
              data,
              url:
                config.url,
              method:
                config.method?.toUpperCase(),
            }
          )
        );
      }
    }

    // ==========================================================
    // 4. 业务错误
    // ==========================================================

    if (
      data?.code ===
      ResultEnum.ERROR
    ) {
      const message =
        data.msg ||
        "请求错误";

      ElMessage.error(
        message
      );

      return Promise.reject(
        new HttpError(
          message,
          data.code,
          {
            data,
            url:
              config?.url,
            method:
              config?.method?.toUpperCase(),
          }
        )
      );
    }

    if (
      data?.code ===
      ResultEnum.UNAUTHORIZED
    ) {
      const message =
        data.msg ||
        "暂无权限";

      ElMessage.error(
        message
      );

      return Promise.reject(
        new HttpError(
          message,
          data.code,
          {
            data,
            url:
              config?.url,
            method:
              config?.method?.toUpperCase(),
          }
        )
      );
    }

    if (
      data?.code ===
      ResultEnum.EXCEPTION
    ) {
      const message =
        data.msg ||
        "服务异常";

      ElMessage.error(
        message
      );

      return Promise.reject(
        new HttpError(
          message,
          data.code,
          {
            data,
            url:
              config?.url,
            method:
              config?.method?.toUpperCase(),
          }
        )
      );
    }

    // ==========================================================
    // 5. 未知错误
    // ==========================================================

    const message =
      data?.msg ||
      getErrorMessage(
        status
      );

    ElMessage.error(
      message
    );

    return Promise.reject(
      new HttpError(
        message,
        status,
        {
          data,
          url:
            config?.url,
          method:
            config?.method?.toUpperCase(),
        }
      )
    );
  }
);

export type {
  AxiosInstance,
} from "axios";

export default request;

