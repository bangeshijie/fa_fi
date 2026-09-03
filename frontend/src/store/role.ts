/**
 * 角色 Store
 *
 * 负责：
 *
 * 1. 角色列表查询
 * 2. 角色分页
 * 3. 角色 CRUD
 * 4. 角色状态修改
 * 5. 角色权限配置
 * 6. 角色详情
 * 7. 角色管理页面搜索状态
 * 8. 角色权限配置状态
 */

import { defineStore } from "pinia";
import { ref } from "vue";

import RoleAPI from "@/api/module_system/role";

import type {
  RoleTable,
  RoleForm,
  RoleExportQuery,
  TablePageQuery,
  PermissionDataType,
} from "@/api/module_system/role";

export const useRoleStore = defineStore(
  "roleStore",
  () => {
    // =========================================================
    // 角色管理
    // =========================================================

    const roleList =
      ref<RoleTable[]>([]);

    const loading =
      ref(false);

    const total =
      ref(0);

    const pageNo =
      ref(1);

    const pageSize =
      ref(10);

    // =========================================================
    // 搜索条件
    // =========================================================

    const searchName =
      ref("");

    const searchStatus =
      ref("");

    const searchCreatedTime =
      ref<string[]>([]);

    const searchUpdatedTime =
      ref<string[]>([]);

    // =========================================================
    // 权限配置
    // =========================================================

    const permissionRole =
      ref<RoleTable | null>(null);

    const permissionDataScope =
      ref<number>(1);

    const permissionRoleIds =
      ref<number[]>([]);

    const permissionMenuIds =
      ref<number[]>([]);

    const permissionDeptIds =
      ref<number[]>([]);

    const permissionLoading =
      ref(false);

    // =========================================================
    // 查询角色
    // =========================================================

    async function fetchRoleList() {
      loading.value = true;

      try {
        const params: TablePageQuery = {
          page_no:
            pageNo.value,

          page_size:
            pageSize.value,
        };

        if (
          searchName.value.trim()
        ) {
          params.name =
            searchName.value.trim();
        }

        if (
          searchStatus.value
        ) {
          params.status =
            searchStatus.value;
        }

        if (
          searchCreatedTime.value
            .length === 2
        ) {
          params.created_time =
            searchCreatedTime.value;
        }

        if (
          searchUpdatedTime.value
            .length === 2
        ) {
          params.updated_time =
            searchUpdatedTime.value;
        }

        const response =
          await RoleAPI.listRole(
            params
          );

        const result =
          response.data.data;

        roleList.value =
          result?.items ?? [];

        total.value =
          result?.total ?? 0;

        return roleList.value;
      } finally {
        loading.value =
          false;
      }
    }

    // =========================================================
    // 分页
    // =========================================================

    async function setPageNo(
      value: number
    ) {
      pageNo.value =
        value;

      await fetchRoleList();
    }

    async function setPageSize(
      value: number
    ) {
      pageSize.value =
        value;

      pageNo.value =
        1;

      await fetchRoleList();
    }

    // =========================================================
    // 创建
    // =========================================================

    async function createRole(
      form: RoleForm
    ) {
      await RoleAPI.createRole(
        form
      );

      await fetchRoleList();
    }

    // =========================================================
    // 修改
    // =========================================================

    async function updateRole(
      id: number,
      form: RoleForm
    ) {
      await RoleAPI.updateRole(
        id,
        form
      );

      await fetchRoleList();
    }

    // =========================================================
    // 删除
    // =========================================================

    async function deleteRole(
      ids: number[]
    ) {
      await RoleAPI.deleteRole(
        ids
      );

      if (
        roleList.value.length ===
          ids.length &&
        pageNo.value > 1
      ) {
        pageNo.value -= 1;
      }

      await fetchRoleList();
    }

    // =========================================================
    // 修改状态
    // =========================================================

    async function updateRoleStatus(
      ids: number[],
      status: string
    ) {
      await RoleAPI.batchRole({
        ids,
        status,
      });

      await fetchRoleList();
    }

    // =========================================================
    // 获取详情
    // =========================================================

    async function getRoleDetail(
      id: number
    ) {
      const response =
        await RoleAPI.detailRole(
          id
        );

      return response.data.data;
    }

    // =========================================================
    // 初始化权限
    // =========================================================

    function initPermission(
      role: RoleTable
    ) {
      permissionRole.value =
        role;

      permissionRoleIds.value =
        [role.id];

      permissionDataScope.value =
        role.data_scope ?? 1;

      permissionMenuIds.value =
        role.menus?.map(
          item => item.id
        ) ?? [];

      permissionDeptIds.value =
        role.depts?.map(
          item => item.id
        ) ?? [];
    }

    // =========================================================
    // 设置权限角色
    // =========================================================

    function setPermissionRole(
      role: RoleTable | null
    ) {
      if (!role) {
        clearPermissionState();

        return;
      }

      initPermission(role);
    }

    // =========================================================
    // 设置数据权限
    // =========================================================

    function setPermissionDataScope(
      value:
        string |
        number |
        boolean |
        undefined
    ) {
      /*
       * Element Plus 的 el-radio-group
       * change 参数类型比较宽。
       *
       * 只有 number 才是我们的合法数据权限值。
       */
      if (
        typeof value !==
        "number"
      ) {
        return;
      }

      permissionDataScope.value =
        value;

      /*
       * 非自定义数据权限，
       * 不需要部门权限。
       */
      if (value !== 5) {
        permissionDeptIds.value =
          [];
      }
    }

    // =========================================================
    // 设置菜单
    // =========================================================

    function setPermissionMenuIds(
      ids: number[]
    ) {
      permissionMenuIds.value =
        ids;
    }

    // =========================================================
    // 设置部门
    // =========================================================

    function setPermissionDeptIds(
      ids: number[]
    ) {
      permissionDeptIds.value =
        ids;
    }

    // =========================================================
    // 设置角色
    // =========================================================

    function setPermissionRoleIds(
      ids: number[]
    ) {
      permissionRoleIds.value =
        ids;
    }

    // =========================================================
    // 保存权限
    // =========================================================

    async function setPermission(
      data?: Partial<PermissionDataType>
    ) {
      permissionLoading.value =
        true;

      try {
        const payload: PermissionDataType =
          {
            data_scope:
              data?.data_scope ??
              permissionDataScope.value,

            role_ids:
              data?.role_ids ??
              permissionRoleIds.value,

            menu_ids:
              data?.menu_ids ??
              permissionMenuIds.value,

            dept_ids:
              data?.dept_ids ??
              permissionDeptIds.value,
          };

        await RoleAPI.setPermission(
          payload
        );

        await fetchRoleList();

        /*
         * 保存成功后重新获取当前角色详情。
         */
        if (
          permissionRole.value?.id
        ) {
          const role =
            await getRoleDetail(
              permissionRole.value.id
            );

          if (role) {
            initPermission(
              role
            );
          }
        }

        return payload;
      } finally {
        permissionLoading.value =
          false;
      }
    }

    async function savePermission() {
      return await setPermission();
    }

    // =========================================================
    // 导出
    // =========================================================

    async function exportRole() {
      /*
       * 注意这里不是 TablePageQuery。
       *
       * 导出不需要：
       * page_no
       * page_size
       */
      const params: RoleExportQuery =
        {};

      if (
        searchName.value.trim()
      ) {
        params.name =
          searchName.value.trim();
      }

      if (
        searchStatus.value
      ) {
        params.status =
          searchStatus.value;
      }

      if (
        searchCreatedTime.value
          .length === 2
      ) {
        params.created_time =
          searchCreatedTime.value;
      }

      if (
        searchUpdatedTime.value
          .length === 2
      ) {
        params.updated_time =
          searchUpdatedTime.value;
      }

      return await RoleAPI.exportRole(
        params
      );
    }

    // =========================================================
    // 搜索
    // =========================================================

    function resetSearch() {
      searchName.value =
        "";

      searchStatus.value =
        "";

      searchCreatedTime.value =
        [];

      searchUpdatedTime.value =
        [];

      pageNo.value =
        1;
    }

    async function resetSearchAndFetch() {
      resetSearch();

      await fetchRoleList();
    }

    // =========================================================
    // 清理权限
    // =========================================================

    function clearPermissionState() {
      permissionRole.value =
        null;

      permissionDataScope.value =
        1;

      permissionRoleIds.value =
        [];

      permissionMenuIds.value =
        [];

      permissionDeptIds.value =
        [];
    }

    // =========================================================
    // 清理角色管理状态
    // =========================================================

    function clearRoleManagementState() {
      roleList.value =
        [];

      total.value =
        0;

      pageNo.value =
        1;

      resetSearch();

      clearPermissionState();
    }

    // =========================================================
    // Return
    // =========================================================

    return {
      // 角色
      roleList,
      loading,
      total,

      // 分页
      pageNo,
      pageSize,

      // 搜索
      searchName,
      searchStatus,
      searchCreatedTime,
      searchUpdatedTime,

      // 权限
      permissionRole,
      permissionDataScope,
      permissionRoleIds,
      permissionMenuIds,
      permissionDeptIds,
      permissionLoading,

      // 查询
      fetchRoleList,

      // 分页
      setPageNo,
      setPageSize,

      // CRUD
      createRole,
      updateRole,
      deleteRole,
      updateRoleStatus,
      getRoleDetail,

      // 权限
      initPermission,
      setPermissionRole,
      setPermissionDataScope,
      setPermissionMenuIds,
      setPermissionDeptIds,
      setPermissionRoleIds,
      setPermission,
      savePermission,

      // 导出
      exportRole,

      // 搜索
      resetSearch,
      resetSearchAndFetch,

      // 清理
      clearPermissionState,
      clearRoleManagementState,
    };
  }
);