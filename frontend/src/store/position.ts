/**
 * 岗位 Store
 *
 * 负责：
 *
 * 1. 岗位列表查询
 * 2. 岗位分页
 * 3. 岗位 CRUD
 * 4. 岗位状态修改
 * 5. 岗位详情
 * 6. 岗位搜索状态
 * 7. 岗位导出
 */

import { defineStore } from "pinia";
import { ref } from "vue";

import PositionAPI from "@/api/module_system/position";

import type {
  PositionTable,
  PositionForm,
    PositionPageQuery,
  PositionExportQuery
} from "@/api/module_system/position";

export const usePositionStore = defineStore(
  "positionStore",
  () => {
    // =========================================================
    // 岗位管理
    // =========================================================

    /** 岗位列表 */
    const positionList =
      ref<PositionTable[]>([]);

    /** 加载状态 */
    const loading =
      ref(false);

    /** 总数量 */
    const total =
      ref(0);

    /** 当前页 */
    const pageNo =
      ref(1);

    /** 每页数量 */
    const pageSize =
      ref(10);

    // =========================================================
    // 搜索条件
    // =========================================================

    /** 岗位名称 */
    const searchName =
      ref("");

    /** 岗位状态 */
    const searchStatus =
      ref("");

    /** 创建时间 */
    const searchCreatedTime =
      ref<string[]>([]);

    /** 更新时间 */
    const searchUpdatedTime =
      ref<string[]>([]);

    // =========================================================
    // 查询岗位
    // =========================================================

    async function fetchPositionList() {
      loading.value = true;

      try {
        /*
         * 列表查询必须包含分页参数。
         */
        const params: PositionPageQuery = {
          page_no:
            pageNo.value,

          page_size:
            pageSize.value,
        };

        // -----------------------------------------------------
        // 岗位名称
        // -----------------------------------------------------

        if (
          searchName.value.trim()
        ) {
          params.name =
            searchName.value.trim();
        }

        // -----------------------------------------------------
        // 状态
        // -----------------------------------------------------

        if (
          searchStatus.value
        ) {
          params.status =
            searchStatus.value;
        }

        // -----------------------------------------------------
        // 创建时间
        // -----------------------------------------------------

        if (
          searchCreatedTime.value
            .length === 2
        ) {
          params.created_time =
            searchCreatedTime.value;
        }

        // -----------------------------------------------------
        // 更新时间
        // -----------------------------------------------------

        if (
          searchUpdatedTime.value
            .length === 2
        ) {
          params.updated_time =
            searchUpdatedTime.value;
        }

        const response =
          await PositionAPI.listPosition(
            params
          );

        const result =
          response.data.data;

        /*
         * 根据你当前项目的 PageResult 结构：
         *
         * {
         *   items: [],
         *   total: 0
         * }
         */
        positionList.value =
          result?.items || [];

        total.value =
          result?.total || 0;

        return positionList.value;
      } finally {
        loading.value = false;
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

      await fetchPositionList();
    }

    async function setPageSize(
      value: number
    ) {
      pageSize.value =
        value;

      pageNo.value =
        1;

      await fetchPositionList();
    }

    // =========================================================
    // 创建
    // =========================================================

    async function createPosition(
      form: PositionForm
    ) {
      await PositionAPI.createPosition(
        form
      );

      await fetchPositionList();
    }

    // =========================================================
    // 修改
    // =========================================================

    async function updatePosition(
      id: number,
      form: PositionForm
    ) {
      await PositionAPI.updatePosition(
        id,
        form
      );

      await fetchPositionList();
    }

    // =========================================================
    // 删除
    // =========================================================

    async function deletePosition(
      ids: number[]
    ) {
      await PositionAPI.deletePosition(
        ids
      );

      /*
       * 如果删除后当前页没有数据，
       * 自动回到上一页。
       */
      if (
        positionList.value
          .length === ids.length &&
        pageNo.value > 1
      ) {
        pageNo.value -= 1;
      }

      await fetchPositionList();
    }

    // =========================================================
    // 修改状态
    // =========================================================

    async function updatePositionStatus(
      ids: number[],
      status: string
    ) {
      await PositionAPI.batchPosition({
        ids,
        status,
      });

      await fetchPositionList();
    }

    // =========================================================
    // 获取详情
    // =========================================================

    async function getPositionDetail(
      id: number
    ) {
      const response =
        await PositionAPI.detailPosition(
          id
        );

      return response.data.data;
    }

    // =========================================================
    // 导出
    // =========================================================

      async function exportPosition() {
                
        const params: PositionExportQuery = {};

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

        if (
            searchUpdatedTime.value.length === 2
        ) {
            params.updated_time =
            searchUpdatedTime.value;
        }

        const response = await PositionAPI.exportPosition(
            params
          );
          return response.data;
          
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

      await fetchPositionList();
    }

    // =========================================================
    // 清理状态
    // =========================================================

    function clearPositionManagementState() {
      positionList.value =
        [];

      total.value =
        0;

      pageNo.value =
        1;

      resetSearch();
    }

    // =========================================================
    // return
    // =========================================================

    return {
      // 列表
      positionList,
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

      // 查询
      fetchPositionList,

      // 分页
      setPageNo,
      setPageSize,

      // CRUD
      createPosition,
      updatePosition,
      deletePosition,
      updatePositionStatus,
      getPositionDetail,

      // 导出
      exportPosition,

      // 搜索
      resetSearch,
      resetSearchAndFetch,

      // 清理
      clearPositionManagementState,
    };
  }
);