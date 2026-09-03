/**
 * 菜单 Store
 *
 * 同时负责：
 *
 * 1. 系统侧边栏使用的菜单状态
 * 2. 菜单管理页面的 CRUD 状态
 * 3. 动态路由相关状态
 */

import { defineStore } from "pinia";
import { ref } from "vue";

import type { AppRouteRecord } from "@/types/router";
import { HOME_PAGE_PATH } from "@/router";

import MenuAPI from "@/api/module_system/menu";
import type {
  MenuTable,
  MenuForm,
  MenuPageQuery,
} from "@/api/module_system/menu";

export const useMenuStore = defineStore(
  "menuStore",
  () => {
    // =========================================================
    // 动态路由 / 系统菜单
    // =========================================================

    /** 首页路径 */
    const homePath = ref(HOME_PAGE_PATH);

    /** 动态路由菜单 */
    const menuList = ref<AppRouteRecord[]>([]);

    /** 菜单宽度 */
    const menuWidth = ref("");

    /** 动态路由移除函数 */
    const removeRouteFns = ref<(() => void)[]>([]);

    // =========================================================
    // 菜单管理页面
    // =========================================================

    /** 菜单管理树 */
    const menuTree = ref<MenuTable[]>([]);

    /** 当前终端未筛选的完整菜单树，用于父菜单选择 */
    const allMenuTree = ref<MenuTable[]>([]);

    /** 菜单管理加载状态 */
    const loading = ref(false);

    /** 当前终端 */
    const currentClient = ref<"pc" | "app">("pc");

    /** 菜单搜索名称 */
    const searchName = ref("");

    /** 菜单状态筛选 */
    const searchStatus = ref<string>("");

    /** 菜单类型筛选 */
    const searchType = ref<number | undefined>(undefined);

    /** 路由地址筛选 */
    const searchRoutePath = ref("");

    // =========================================================
    // 首页
    // =========================================================

    const getHomePath = () => {
      return homePath.value;
    };

    const setHomePath = (path: string) => {
      homePath.value = path;
    };

    // =========================================================
    // 动态路由
    // =========================================================

    const addRemoveRouteFns = (
      fns: (() => void)[]
    ) => {
      removeRouteFns.value.push(...fns);
    };

    const removeAllDynamicRoutes = () => {
      removeRouteFns.value.forEach((fn) => fn());
      removeRouteFns.value = [];
    };

    const clearRemoveRouteFns = () => {
      removeRouteFns.value = [];
    };

    // =========================================================
    // 菜单管理
    // =========================================================

    /**
     * 查询菜单树
     */
    async function fetchMenuTree() {
      loading.value = true;

      try {
        const params: MenuPageQuery & {
          type?: number;
        } = {
          menu_client: currentClient.value,
        };

        if (searchName.value.trim()) {
          params.name = searchName.value.trim();
        }

        if (searchStatus.value) {
          params.status = searchStatus.value;
        }

        if (searchType.value !== undefined) {
          params.type = searchType.value;
        }

        if (searchRoutePath.value.trim()) {
          params.route_path = searchRoutePath.value.trim();
        }

        const response = await MenuAPI.listMenu(params);

        menuTree.value = response.data.data || [];

        return menuTree.value;
      } finally {
        loading.value = false;
      }
    }

    async function fetchAllMenuTree() {
      const response = await MenuAPI.listMenu({
        menu_client: currentClient.value,
      });
      allMenuTree.value = response.data.data || [];
      return allMenuTree.value;
    }

    async function refreshMenuData() {
      await Promise.all([
        fetchMenuTree(),
        fetchAllMenuTree(),
      ]);
    }

    /**
     * 切换 PC / APP
     */
    async function setClient(
      client: "pc" | "app"
    ) {
      currentClient.value = client;

      await refreshMenuData();
    }

    /**
     * 创建菜单
     */
    async function createMenu(
      form: MenuForm
    ) {
      await MenuAPI.createMenu(form);

      await refreshMenuData();
    }

    /**
     * 修改菜单
     */
    async function updateMenu(
      id: number,
      form: MenuForm
    ) {
      await MenuAPI.updateMenu(id, form);

      await refreshMenuData();
    }

    /**
     * 删除菜单
     */
    async function deleteMenu(
      ids: number[]
    ) {
      await MenuAPI.deleteMenu(ids);

      await refreshMenuData();
    }

    /**
     * 修改菜单状态
     *
     * 这里不依赖 batchMenu 的 BatchType 类型，
     * 直接通过已有 updateMenu 接口修改 status。
     */
    async function updateMenuStatus(
      row: MenuTable,
      status: string
    ) {
      if (!row.id) {
        return;
      }

      const payload = {
        name: row.name || "",
        type: row.type || 2,
        order: row.order || 1,
        permission: row.permission || undefined,
        icon: row.icon || undefined,
        route_name: row.route_name || undefined,
        route_path: row.route_path || undefined,
        component_path: row.component_path || undefined,
        redirect: row.redirect || undefined,
        hidden: row.hidden ?? false,
        keep_alive: row.keep_alive ?? true,
        always_show: row.always_show ?? false,
        title: row.title || undefined,
        params: row.params || undefined,
        affix: row.affix ?? false,
        parent_id: row.parent_id || undefined,
        status,
        description: row.description || undefined,
        client: row.client || currentClient.value,
      };

      await MenuAPI.updateMenu(
        row.id,
        payload as MenuForm
      );

      await refreshMenuData();
    }

    /**
     * 获取菜单详情
     */
    async function getMenuDetail(
      id: number
    ) {
      const response =
        await MenuAPI.detailMenu(id);

      return response.data.data;
    }

    /**
     * 清空菜单管理状态
     */
    function clearMenuManagementState() {
      menuTree.value = [];
      allMenuTree.value = [];
      searchName.value = "";
      searchStatus.value = "";
      searchType.value = undefined;
      searchRoutePath.value = "";
    }

    return {
      // 动态菜单
      menuList,
      menuWidth,
      removeRouteFns,

      getHomePath,
      setHomePath,

      addRemoveRouteFns,
      removeAllDynamicRoutes,
      clearRemoveRouteFns,

      // 菜单管理
      menuTree,
      allMenuTree,
      loading,

      currentClient,
      searchName,
      searchStatus,
      searchType,
      searchRoutePath,

      fetchMenuTree,
      fetchAllMenuTree,
      refreshMenuData,
      setClient,

      createMenu,
      updateMenu,
      deleteMenu,
      updateMenuStatus,
      getMenuDetail,

      clearMenuManagementState,
    };
  },
  {
    persist: {
      pick: [
        "homePath",
        "menuWidth",
      ],
    },
  }
);
