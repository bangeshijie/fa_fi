/**
 * 部门 Store
 *
 * 负责：
 *
 * 1. 部门树查询
 * 2. 部门 CRUD
 * 3. 部门状态修改
 * 4. 部门管理页面搜索状态
 */

import { defineStore } from "pinia";
import { ref } from "vue";

import DeptAPI from "@/api/module_system/dept";

import type {
  DeptTable,
  DeptForm,
  DeptPageQuery,
} from "@/api/module_system/dept";

export const useDeptStore = defineStore(
  "deptStore",
  () => {
    // =========================================================
    // 部门管理
    // =========================================================

    /** 部门树 */
    const deptTree = ref<DeptTable[]>([]);

    /** 未筛选的完整部门树，用于新增/编辑时选择上级部门 */
    const allDeptTree = ref<DeptTable[]>([]);

    /** 加载状态 */
    const loading = ref(false);

    /** 部门名称搜索 */
    const searchName = ref("");

    /** 部门状态 */
    const searchStatus = ref<string>("");

    /** 创建时间 */
    const searchCreatedTime =
      ref<string[]>([]);

    // =========================================================
    // 查询部门树
    // =========================================================

    async function fetchDeptTree() {
      loading.value = true;

      try {
        const params: DeptPageQuery = {};

        if (searchName.value.trim()) {
          params.name =
            searchName.value.trim();
        }

        if (searchStatus.value) {
          params.status =
            searchStatus.value;
        }

        if (
          searchCreatedTime.value.length === 2
        ) {
          params.created_time =
            searchCreatedTime.value;
        }

        const response =
          await DeptAPI.listDept(params);

        deptTree.value =
          response.data.data || [];

        return deptTree.value;
      } finally {
        loading.value = false;
      }
    }

    async function fetchAllDeptTree() {
      const response = await DeptAPI.listDept();
      allDeptTree.value = response.data.data || [];
      return allDeptTree.value;
    }

    async function refreshDeptData() {
      await Promise.all([
        fetchDeptTree(),
        fetchAllDeptTree(),
      ]);
    }

    // =========================================================
    // 创建
    // =========================================================

    async function createDept(
      form: DeptForm
    ) {
      await DeptAPI.createDept(form);

      await refreshDeptData();
    }

    // =========================================================
    // 修改
    // =========================================================

    async function updateDept(
      id: number,
      form: DeptForm
    ) {
      await DeptAPI.updateDept(
        id,
        form
      );

      await refreshDeptData();
    }

    // =========================================================
    // 删除
    // =========================================================

    async function deleteDept(
      ids: number[]
    ) {
      await DeptAPI.deleteDept(ids);

      await refreshDeptData();
    }

    // =========================================================
    // 批量修改状态
    // =========================================================

    async function updateDeptStatus(
      ids: number[],
      status: string
    ) {
      await DeptAPI.batchDept({
        ids,
        status,
      });

      await refreshDeptData();
    }

    // =========================================================
    // 获取详情
    // =========================================================

    async function getDeptDetail(
      id: number
    ) {
      const response =
        await DeptAPI.detailDept(id);

      return response.data.data;
    }

    // =========================================================
    // 重置搜索
    // =========================================================

    function resetSearch() {
      searchName.value = "";
      searchStatus.value = "";
      searchCreatedTime.value = [];
    }

    // =========================================================
    // 清空
    // =========================================================

    function clearDeptState() {
      deptTree.value = [];
      allDeptTree.value = [];

      resetSearch();
    }

    return {
      deptTree,
      allDeptTree,
      loading,

      searchName,
      searchStatus,
      searchCreatedTime,

      fetchDeptTree,
      fetchAllDeptTree,
      refreshDeptData,

      createDept,
      updateDept,
      deleteDept,

      updateDeptStatus,

      getDeptDetail,

      resetSearch,
      clearDeptState,
    };
  }
);
