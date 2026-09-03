/**
 * Auth 认证令牌管理
 *
 * 设计：
 *
 * Access Token
 * ├── 用于正常 API 请求
 * ├── 短生命周期
 * └── 过期后由 Axios 自动使用 Refresh Token 刷新
 *
 * Refresh Token
 * ├── 只用于 /auth/token/refresh
 * ├── 生命周期比 Access Token 长
 * └── 每次刷新成功后由后端返回新的 Refresh Token
 *
 * rememberMe
 * ├── true  -> localStorage
 * └── false -> sessionStorage
 *
 * 注意：
 * 这里不负责判断 JWT 是否过期。
 * JWT 是否过期由后端 + Axios 401 拦截机制共同处理。
 *
 * @module Auth
 */

const AUTH_KEYS = {
  ACCESS_TOKEN: "access_token",
  REFRESH_TOKEN: "refresh_token",
  REMEMBER_ME: "remember_me",
} as const;

/**
 * Token 存储位置
 */
type StorageType = Storage;

/**
 * Auth 类
 */
export class Auth {
  /**
   * 当前是否存在 Access Token
   *
   * 注意：
   * 这里只判断本地是否存在 token，
   * 不代表 token 一定有效。
   */
  static isLoggedIn(): boolean {
    return !!Auth.getAccessToken();
  }

  /**
   * 获取当前使用的 Storage
   *
   * rememberMe = true
   *   localStorage
   *
   * rememberMe = false
   *   sessionStorage
   */
  private static getStorage(): StorageType {
    return Auth.getRememberMe()
      ? localStorage
      : sessionStorage;
  }

  /**
   * 获取 Access Token
   */
  static getAccessToken(): string {
    const storage = Auth.getStorage();

    return (
      storage.getItem(AUTH_KEYS.ACCESS_TOKEN) || ""
    );
  }

  /**
   * 获取 Refresh Token
   */
  static getRefreshToken(): string {
    const storage = Auth.getStorage();

    return (
      storage.getItem(AUTH_KEYS.REFRESH_TOKEN) || ""
    );
  }

  /**
   * 获取 rememberMe 状态
   */
  static getRememberMe(): boolean {
    return (
      localStorage.getItem(
        AUTH_KEYS.REMEMBER_ME
      ) === "true"
    );
  }

  /**
   * 保存 Token
   *
   * 登录成功后调用：
   *
   * Auth.setTokens(
   *   access_token,
   *   refresh_token,
   *   rememberMe
   * )
   *
   * rememberMe = true
   * -----------------
   * localStorage:
   *   access_token
   *   refresh_token
   *
   * rememberMe = false
   * -----------------
   * sessionStorage:
   *   access_token
   *   refresh_token
   */
  static setTokens(
    accessToken: string,
    refreshToken: string,
    rememberMe: boolean
  ): void {
    // 记录 rememberMe
    localStorage.setItem(
      AUTH_KEYS.REMEMBER_ME,
      String(rememberMe)
    );

    if (rememberMe) {
      /**
       * 使用 localStorage
       */

      localStorage.setItem(
        AUTH_KEYS.ACCESS_TOKEN,
        accessToken
      );

      localStorage.setItem(
        AUTH_KEYS.REFRESH_TOKEN,
        refreshToken
      );

      /**
       * 清理 sessionStorage
       *
       * 防止之前非记住登录留下旧 token
       */
      sessionStorage.removeItem(
        AUTH_KEYS.ACCESS_TOKEN
      );

      sessionStorage.removeItem(
        AUTH_KEYS.REFRESH_TOKEN
      );
    } else {
      /**
       * 使用 sessionStorage
       */

      sessionStorage.setItem(
        AUTH_KEYS.ACCESS_TOKEN,
        accessToken
      );

      sessionStorage.setItem(
        AUTH_KEYS.REFRESH_TOKEN,
        refreshToken
      );

      /**
       * 清理 localStorage 中旧 token
       */
      localStorage.removeItem(
        AUTH_KEYS.ACCESS_TOKEN
      );

      localStorage.removeItem(
        AUTH_KEYS.REFRESH_TOKEN
      );
    }
  }

  /**
   * 只更新 Access Token
   *
   * 某些场景如果后端只返回 Access Token，
   * 可以单独调用这个方法。
   */
  static setAccessToken(
    accessToken: string
  ): void {
    const storage = Auth.getStorage();

    storage.setItem(
      AUTH_KEYS.ACCESS_TOKEN,
      accessToken
    );
  }

  /**
   * 只更新 Refresh Token
   */
  static setRefreshToken(
    refreshToken: string
  ): void {
    const storage = Auth.getStorage();

    storage.setItem(
      AUTH_KEYS.REFRESH_TOKEN,
      refreshToken
    );
  }

  /**
   * 清除 Access Token
   */
  static clearAccessToken(): void {
    localStorage.removeItem(
      AUTH_KEYS.ACCESS_TOKEN
    );

    sessionStorage.removeItem(
      AUTH_KEYS.ACCESS_TOKEN
    );
  }

  /**
   * 清除 Refresh Token
   */
  static clearRefreshToken(): void {
    localStorage.removeItem(
      AUTH_KEYS.REFRESH_TOKEN
    );

    sessionStorage.removeItem(
      AUTH_KEYS.REFRESH_TOKEN
    );
  }

  /**
   * 清除全部认证信息
   *
   * 登录失效、退出登录、Refresh Token 失效时调用。
   */
  static clearAuth(): void {
    /**
     * 清理 localStorage
     */
    localStorage.removeItem(
      AUTH_KEYS.ACCESS_TOKEN
    );

    localStorage.removeItem(
      AUTH_KEYS.REFRESH_TOKEN
    );

    localStorage.removeItem(
      AUTH_KEYS.REMEMBER_ME
    );

    /**
     * 清理 sessionStorage
     */
    sessionStorage.removeItem(
      AUTH_KEYS.ACCESS_TOKEN
    );

    sessionStorage.removeItem(
      AUTH_KEYS.REFRESH_TOKEN
    );
  }

  /**
   * 判断是否存在 Refresh Token
   *
   * 这个方法主要给 Axios 刷新逻辑使用。
   */
  static hasRefreshToken(): boolean {
    return !!Auth.getRefreshToken();
  }

  /**
   * 判断当前认证信息是否完整
   */
  static hasValidAuthStorage(): boolean {
    return (
      !!Auth.getAccessToken() &&
      !!Auth.getRefreshToken()
    );
  }

  /**
   * 获取当前认证信息
   *
   * 主要用于调试。
   *
   * 注意：
   * 不建议打印 token 到生产环境日志。
   */
  static getAuthInfo(): {
    accessToken: string;
    refreshToken: string;
    rememberMe: boolean;
  } {
    return {
      accessToken: Auth.getAccessToken(),
      refreshToken: Auth.getRefreshToken(),
      rememberMe: Auth.getRememberMe(),
    };
  }
}

/**
 * 导出固定 Key
 *
 * 如果其他地方需要清理或者判断 key，
 * 可以直接使用 AUTH_KEYS。
 */
export { AUTH_KEYS };

/**
 * 登录失效跳转处理
 *
 * 这里单独放在 Auth 模块中，
 * 保持你目前 Axios 的调用方式：
 *
 * import {
 *   Auth,
 *   redirectToLogin
 * } from "@/utils/auth";
 */

import { router } from "@/router";
import { useAuthStore } from "@/store/auth";
import {
  ElMessage,
  ElNotification,
} from "element-plus";

/**
 * 登录页跳转进行中
 *
 * 防止多个接口同时 401：
 *
 * 请求 A -> 401
 * 请求 B -> 401
 * 请求 C -> 401
 *
 * 最终只跳一次登录页面。
 */
let redirectToLoginInFlight:
  Promise<void> | null = null;

/**
 * 跳转登录页面
 *
 * 功能：
 *
 * 1. 显示提示
 * 2. 清理 Pinia 用户状态
 * 3. 清理 token
 * 4. 保存当前页面地址
 * 5. 跳转登录页
 */
export async function redirectToLogin(
  message: string = "请重新登录"
): Promise<void> {
  /**
   * 已经有跳转任务
   *
   * 直接等待之前的任务。
   */
  if (redirectToLoginInFlight) {
    return redirectToLoginInFlight;
  }

  redirectToLoginInFlight =
    (async () => {
      try {
        /**
         * 提示用户
         */
        ElNotification({
          title: "提示",
          message,
          type: "warning",
          duration: 3000,
        });

        /**
         * 获取当前页面
         *
         * 注意：
         * 在清理状态之前获取。
         */
        const currentPath =
          router.currentRoute.value.fullPath;

        /**
         * 清理用户状态
         *
         * 你的 user store 中应该负责：
         *
         * - 用户信息
         * - 菜单
         * - 权限
         * - Token
         * - 其他登录状态
         *
         * 如果 resetAllState() 内部已经调用
         * Auth.clearAuth()，这里就不用重复调用。
         */
        await useAuthStore().resetAllState();

        /**
         * 双保险：
         *
         * 即使 resetAllState() 没有清 Token，
         * 这里也确保 token 被清掉。
         */
        Auth.clearAuth();

        /**
         * 如果已经在登录页，
         * 不再重复 push。
         */
        if (
          router.currentRoute.value.path !==
          "/login"
        ) {
          await router.push({
            path: "/login",
            query: {
              redirect: currentPath,
            },
          });
        }
      } catch (error: unknown) {
        const message =
          error instanceof Error
            ? error.message
            : String(error);

        ElMessage.error(message);
      } finally {
        /**
         * 当前跳转任务完成
         */
        redirectToLoginInFlight = null;
      }
    })();

  return redirectToLoginInFlight;
}