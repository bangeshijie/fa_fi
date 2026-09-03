/** User store */
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { router } from "@/router";

import { useTabsStore } from "./tabs";
import { useMenuStore } from "./menu";

import type { AppRouteRecord } from "@/types/router";
import type { UserInfo } from "@/api/module_system/user";

import { Auth } from "@/utils";
import AuthAPI from "@/api/module_system/auth";
import UserAPI from "@/api/module_system/user";

import { resetRouter } from "@/router/permission";

/**
 * 登出参数
 */
export interface LogoutOptions {
  /**
   * 是否跳转登录页
   *
   * true  -> 清理状态后跳转登录
   * false -> 只清理状态，不跳转
   *
   * @default true
   */
  navigate?: boolean;
}

export interface OAuthLoginToken {
  access_token: string;
  refresh_token: string;
  token_type?: string;
}

/**
 * 用户状态管理
 *
 * 主要负责：
 *
 * 1. Token
 * 2. 用户信息
 * 3. 动态路由
 * 4. 权限
 * 5. 登录
 * 6. 登出
 * 7. 路由状态重置
 */
export const useAuthStore = defineStore(
  "authStore",
  () => {
    /**
     * =========================================================
     * Token
     * =========================================================
     */

    /**
     * Access Token
     */
    const accessToken = ref<string>("");

    /**
     * Refresh Token
     */
    const refreshToken = ref<string>("");

    /**
     * =========================================================
     * 用户信息
     * =========================================================
     */

    const info = ref<Partial<UserInfo>>({});

    /**
     * 登录状态
     */
    const isLogin = ref(false);

    /**
     * =========================================================
     * 动态路由
     * =========================================================
     */

    /**
     * 后端菜单转换后的路由
     */

    

    const routeList = ref<AppRouteRecord[]>([]);

    /**
     * 是否已经获取用户信息和动态路由
     *
     * false：
     *     还没有初始化用户路由
     *
     * true：
     *     用户信息、菜单、动态路由已经完成初始化
     */
    const hasGetRoute = ref(false);

    /**
     * =========================================================
     * 权限
     * =========================================================
     */

    /**
     * 当前用户拥有的权限标识
     *
     * 例如：
     *
     * module_system:menu:create
     * module_system:menu:update
     * module_system:menu:delete
     */
    const prems = ref<string[]>([]);

    /**
     * =========================================================
     * 其他状态
     * =========================================================
     */

    /**
     * 搜索历史
     */
    const searchHistory = ref<AppRouteRecord[]>([]);

    /**
     * 记住我
     */
    const rememberMe = ref<boolean>(
      Auth.getRememberMe()
    );

    /**
     * =========================================================
     * Computed
     * =========================================================
     */

    /**
     * 基础用户信息
     */
    type UserInfoLike =
      Partial<UserInfo> &
      Record<string, any>;

    const basicInfo = computed(
      () => info.value as UserInfoLike
    );

    /**
     * 工作台状态
     */
    const getWorktabState = computed(
      () => useTabsStore().$state
    );

    /**
     * =========================================================
     * 设置当前登录用户信息
     * =========================================================
     */

    /** 当前登录用户资料的唯一归属是 authStore。 */
    function setUserInfo(
      newInfo: Partial<UserInfo>
    ) {
      info.value = {
        ...info.value,
        ...newInfo,
      };
    }

    /**
     * =========================================================
     * 设置登录状态
     * =========================================================
     */

    function setLoginStatus(
      status: boolean
    ) {
      isLogin.value = status;
    }

    /**
     * =========================================================
     * 设置搜索历史
     * =========================================================
     */

    function setSearchHistory(
      list: AppRouteRecord[]
    ) {
      searchHistory.value = list;
    }

    /**
     * =========================================================
     * 设置 Token
     * =========================================================
     */

    function setToken(
      newAccessToken: string,
      newRefreshToken?: string
    ) {
      accessToken.value =
        newAccessToken;

      if (
        newRefreshToken !== undefined
      ) {
        refreshToken.value =
          newRefreshToken;
      }
    }

    /**
     * =========================================================
     * 设置头像
     * =========================================================
     */

    function setAvatar(
      avatar: string
    ) {
      info.value = {
        ...info.value,
        avatar,
      };
    }

    /**
     * =========================================================
     * 设置动态路由
     * =========================================================
     *
     * 注意：
     *
     * 这里统一使用 setRoute。
     *
     * setRoute()
     *     ↓
     * routeList
     *     ↓
     * hasGetRoute = true
     */

    function setRoute(
      routes: AppRouteRecord[]
    ) {
      routeList.value = routes;

      hasGetRoute.value = true;
    }

    /**
     * =========================================================
     * 设置权限
     * =========================================================
     *
     * 从动态路由 meta.authMark 中提取权限。
     *
     * 例如：
     *
     * module_system:menu:create
     * module_system:menu:update
     * module_system:menu:delete
     */

    function setPermissions(
      routes: AppRouteRecord[],
      additionalPermissions: string[] = [],
    ) {
      const permissionSet =
        new Set<string>();

      /**
       * 递归收集权限
       */
      function collect(
        items: AppRouteRecord[]
      ) {
        items.forEach(
          (item) => {
            const authMark =
              item.meta?.authMark;

            if (
              typeof authMark === "string" &&
              authMark.trim()
            ) {
              permissionSet.add(
                authMark.trim()
              );
            }

            if (
              Array.isArray(
                item.children
              ) &&
              item.children.length > 0
            ) {
              collect(
                item.children
              );
            }
          }
        );
      }

      collect(routes);

      // type=3 按钮权限不会生成 Vue Router 路由，
      // 需要从后端菜单树单独合并进当前用户权限集合。
      additionalPermissions.forEach(
        (permission) => {
          if (typeof permission === "string" && permission.trim()) {
            permissionSet.add(permission.trim());
          }
        },
      );

      prems.value =
        Array.from(permissionSet);
    }

    /**
     * =========================================================
     * 获取用户信息
     * =========================================================
     *
     * 登录成功：
     *
     * login()
     *   ↓
     * getUserInfo()
     *   ↓
     * 获取用户信息
     *   ↓
     * 获取 menus
     *   ↓
     * generateRoutes()
     *   ↓
     * setRoute()
     *   ↓
     * addDynamicRoutes()
     *   ↓
     * setPermissions()
     */

    /**
     * 只刷新当前登录用户资料，不触碰后台用户列表。
     * 需要动态菜单时由 getUserInfo() 在此基础上继续初始化路由。
     */
    async function fetchCurrentUserInfo() {
      const response =
        await UserAPI.getCurrentUserInfo();

      const data =
        response.data.data;

      const userInfo = {
        ...data,
      };

      delete userInfo.menus;
      setUserInfo(userInfo);

      return data;
    }

    async function getUserInfo() {
      try {
        /**
         * 获取当前用户资料
         */
        const data =
          await fetchCurrentUserInfo();

        /**
         * 后端返回菜单
         */
        const menus =
          data?.menus || [];

        /**
         * 动态导入 permission
         *
         * 避免：
         *
         * user.ts
         * ↓
         * permission.ts
         * ↓
         * user.ts
         *
         * 的循环依赖问题。
         */
        const {
          generateRoutes,
          addDynamicRoutes,
          collectPermissions,
        } = await import(
          "@/router/permission"
        );

        /**
         * 后端菜单
         *
         * ↓
         *
         * Vue Router 路由
         */
        const routes =
          generateRoutes(menus);

        /**
         * 保存路由
         */
        setRoute(routes);

        /**
         * 注册动态路由
         */
        addDynamicRoutes(routes);

        /**
         * 提取权限
         */
        setPermissions(
          routes,
          collectPermissions(menus),
        );

        /**
         * 登录状态
         */
        setLoginStatus(true);

        console.log(
          "[authStore] 用户信息加载完成"
        );

        console.log(
          "[authStore] 动态路由数量:",
          routes.length
        );

        console.log(
          "[authStore] 权限数量:",
          prems.value.length
        );

        return data;
      } catch (error) {
        console.error(
          "[authStore] 获取用户信息失败:",
          error
        );

        /**
         * 一定要继续抛出
         *
         * permission.ts
         * beforeEach()
         *
         * 才能捕获这个异常，
         * 然后跳转登录。
         */
        throw error;
      }
    }

    /**
     * =========================================================
     * 登录
     * =========================================================
     */

    async function login(
      loginForm: any
    ) {
      /**
       * 登录前清理旧动态路由
       *
       * 防止：
       *
       * 用户 A
       * ↓
       * 登出
       * ↓
       * 用户 B
       *
       * 用户 A 的动态路由残留。
       */
      resetRouter();

      /**
       * 清理旧状态
       */
      info.value = {};
      routeList.value = [];
      prems.value = [];
      hasGetRoute.value = false;

      /**
       * 请求登录
       */
      const response =
        await AuthAPI.login(
          loginForm
        );

      const data =
        response.data.data;

      /**
       * 记住我
       */
      rememberMe.value =
        !!loginForm.remember;

      /**
       * Token
       */
      const newAccessToken =
        data?.access_token || "";

      const newRefreshToken =
        data?.refresh_token || "";

      /**
       * 防御
       */
      if (!newAccessToken) {
        console.error(
          "[authStore] 登录成功，但没有 access_token"
        );

        throw new Error(
          "登录失败：未获取到 access_token"
        );
      }

      /**
       * 保存 Token
       *
       * Auth：
       *     localStorage / sessionStorage
       *
       * Pinia：
       *     当前运行时状态
       */
      Auth.setTokens(
        newAccessToken,
        newRefreshToken,
        rememberMe.value
      );

      setToken(
        newAccessToken,
        newRefreshToken
      );

      /**
       * 获取用户信息 + 菜单 + 动态路由
       */
      await getUserInfo();

      /**
       * 登录完成
       */
      setLoginStatus(true);

      console.log(
        "[authStore] 登录完成"
      );
    }

    /**
     * 使用后端 OAuth 回调携带的 Token 完成登录。
     * OAuth 用户已经由后端完成身份交换，这里只负责保存令牌并初始化用户信息、菜单和路由。
     */
    async function loginWithOAuthToken(
      tokenData: OAuthLoginToken,
      remember = true,
    ) {
      resetRouter();
      info.value = {};
      routeList.value = [];
      prems.value = [];
      hasGetRoute.value = false;

      if (!tokenData.access_token || !tokenData.refresh_token) {
        throw new Error("第三方登录未返回完整令牌");
      }

      rememberMe.value = remember;
      Auth.setTokens(
        tokenData.access_token,
        tokenData.refresh_token,
        remember,
      );
      setToken(tokenData.access_token, tokenData.refresh_token);
      await getUserInfo();
      setLoginStatus(true);
    }

    /**
     * =========================================================
     * 刷新 Token
     * =========================================================
     */

    async function refreshTokenFn() {
      const currentRefreshToken =
        Auth.getRefreshToken();

      if (
        !currentRefreshToken
      ) {
        throw new Error(
          "没有有效的刷新令牌"
        );
      }

      try {
        const response =
          await AuthAPI.refreshToken({
            refresh_token:
              currentRefreshToken,
          });

        const data =
          response.data.data;

        const newAccessToken =
          data?.access_token || "";

        const newRefreshToken =
          data?.refresh_token || "";

        if (!newAccessToken) {
          throw new Error(
            "刷新 Token 失败：未返回 access_token"
          );
        }

        /**
         * 更新持久化 Token
         */
        Auth.setTokens(
          newAccessToken,
          newRefreshToken,
          Auth.getRememberMe()
        );

        /**
         * 更新 Pinia
         */
        setToken(
          newAccessToken,
          newRefreshToken
        );

        return newAccessToken;
      } catch (error) {
        console.error(
          "[authStore] 刷新 Token 失败:",
          error
        );

        throw error;
      }
    }

    /**
     * =========================================================
     * 登出
     * =========================================================
     */

    async function logout(
      options?: LogoutOptions
    ) {
      const shouldNavigate =
        options?.navigate !== false;

      /**
       * 当前 Token
       */
      const token =
        Auth.getAccessToken();

      /**
       * 通知后端退出
       */
      if (token) {
        try {
          await AuthAPI.logout({
            token,
          });
        } catch (error) {
          /**
           * 后端退出失败不能阻止前端清理
           */
          console.warn(
            "[authStore] 服务器退出失败:",
            error
          );
        }
      }

      /**
       * 保存当前路由
       *
       * 用于：
       *
       * /home
       * ↓
       * logout
       * ↓
       * /login?redirect=/home
       */
      const currentRoute =
        router.currentRoute.value;

      const redirect =
        currentRoute.path !== "/login"
          ? currentRoute.fullPath
          : undefined;

      /**
       * 清理全部状态
       */
      resetAllState();

      /**
       * 清理 iframe 路由
       */
      sessionStorage.removeItem(
        "iframeRoutes"
      );

      /**
       * 清理首页
       */
      useMenuStore()
        .setHomePath("");

      /**
       * 是否跳转登录
       */
      if (shouldNavigate) {
        await router.push({
          name: "Login",

          query:
            redirect
              ? {
                  redirect,
                }
              : undefined,
        });
      }
    }

    /**
     * =========================================================
     * 重置全部状态
     * =========================================================
     */

    function resetAllState() {
      /**
       * 删除动态路由
       */
      resetRouter();

      /**
       * 清理 Token
       */
      Auth.clearAuth();

      /**
       * 清理用户状态
       */
      info.value = {};

      routeList.value = [];

      prems.value = [];

      hasGetRoute.value = false;

      isLogin.value = false;

      accessToken.value = "";

      refreshToken.value = "";

      /**
       * 清理 Tabs
       */
      useTabsStore()
        .closeAllTabs();
    }

    /**
     * =========================================================
     * 清空用户信息
     * =========================================================
     *
     * 和 resetAllState 的区别：
     *
     * clearUserInfo()
     *     ↓
     * 只清理用户 / 路由信息
     *
     * resetAllState()
     *     ↓
     * Token
     * 路由
     * 权限
     * Tabs
     * 全部清理
     */

    function clearUserInfo() {
      info.value = {};

      routeList.value = [];

      prems.value = [];

      hasGetRoute.value = false;

      isLogin.value = false;
    }

    /**
     * =========================================================
     * 完全重置
     * =========================================================
     *
     * 保留这个方法是为了兼容你项目中
     * 其他地方可能已经调用 fullResetAllState()
     */

    async function fullResetAllState() {
      resetAllState();

      return Promise.resolve();
    }

    /**
     * =========================================================
     * Store 对外暴露
     * =========================================================
     */

    return {
      /**
       * Token
       */
      accessToken,
      refreshToken,

      /**
       * 用户
       */
      info,
      isLogin,
      rememberMe,

      /**
       * 动态路由
       */
      routeList,
      hasGetRoute,

      /**
       * 权限
       */
      prems,

      /**
       * 其他
       */
      searchHistory,

      /**
       * Computed
       */
      basicInfo,
      getWorktabState,

      /**
       * 用户操作
       */
      setUserInfo,
      setLoginStatus,
      setSearchHistory,

      /**
       * Token
       */
      setToken,
      refreshTokenFn,

      /**
       * 用户信息
       */
      fetchCurrentUserInfo,
      getUserInfo,
      setAvatar,

      /**
       * 路由
       */
      setRoute,

      /**
       * 权限
       */
      setPermissions,

      /**
       * 登录
       */
      login,
      loginWithOAuthToken,

      /**
       * 登出
       */
      logout,

      /**
       * 清理
       */
      clearUserInfo,
      resetAllState,
      fullResetAllState,
    };
  },

  /**
   * ===========================================================
   * Pinia 持久化
   * ===========================================================
   *
   * 持久化：
   *
   * accessToken
   * refreshToken
   * info
   * rememberMe
   *
   * 不持久化：
   *
   * routeList
   * hasGetRoute
   * prems
   *
   * 原因：
   *
   * 浏览器刷新以后必须重新根据后端 menus
   * 构建动态路由。
   */
  {
    persist: {
      key: "user",

      storage: localStorage,

      pick: [
        "accessToken",
        "refreshToken",
        "info",
        "rememberMe",
      ],
    },
  }
);
