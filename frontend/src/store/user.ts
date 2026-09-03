/**
 * 用户 Store
 *
 * 负责：
 *
 * 注意：当前登录用户资料不在这里维护。
 * 登录态、Token、当前用户、菜单和权限统一由 authStore 负责；
 * 本 Store 只在“系统管理 > 用户管理”页面按需加载后台用户数据。
 *
 * 1. 后台用户列表查询
 * 2. 用户分页
 * 3. 用户 CRUD
 * 4. 用户状态修改
 * 5. 用户详情
 * 6. 用户搜索状态
 * 7. 用户导出
 * 8. 用户导入
 * 9. 下载导入模板
 * 10. 重置用户密码
 */

import { defineStore } from "pinia";
import { ref } from "vue";

import UserAPI from "@/api/module_system/user";

import type {
    UserInfo,
    UserForm,
    UserPageQuery,
    ResetPasswordForm,
    UserImportResult,
} from "@/api/module_system/user";

export const useUserStore = defineStore(
    "userStore",
    () => {
        // =========================================================
        // 用户管理
        // =========================================================

        /** 用户列表 */
        const userList =
            ref<UserInfo[]>([]);

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

        /** 用户名 */
        const searchUsername =
            ref("");

        /** 姓名 */
        const searchName =
            ref("");

        /** 手机号 */
        const searchMobile =
            ref("");

        /** 邮箱 */
        const searchEmail =
            ref("");

        /** 部门 */
        const searchDeptId =
            ref<number | undefined>(
                undefined
            );

        /** 状态 */
        const searchStatus =
            ref("");

        /** 创建时间 */
        const searchCreatedTime =
            ref<string[]>([]);

        // =========================================================
        // 查询用户
        // =========================================================

        async function fetchUserList() {
            loading.value = true;

            try {
                /*
                 * 列表查询必须包含分页参数。
                 */
                const params:
                    UserPageQuery = {
                    page_no:
                        pageNo.value,

                    page_size:
                        pageSize.value,
                };

                // -------------------------------------------------
                // 用户名
                // -------------------------------------------------

                if (
                    searchUsername.value
                        .trim()
                ) {
                    params.username =
                        searchUsername.value
                            .trim();
                }

                // -------------------------------------------------
                // 姓名
                // -------------------------------------------------

                if (
                    searchName.value
                        .trim()
                ) {
                    params.name =
                        searchName.value
                            .trim();
                }

                // -------------------------------------------------
                // 手机号
                // -------------------------------------------------

                if (
                    searchMobile.value
                        .trim()
                ) {
                    params.mobile =
                        searchMobile.value
                            .trim();
                }

                // -------------------------------------------------
                // 邮箱
                // -------------------------------------------------

                if (
                    searchEmail.value
                        .trim()
                ) {
                    params.email =
                        searchEmail.value
                            .trim();
                }

                // -------------------------------------------------
                // 部门
                // -------------------------------------------------

                if (
                    searchDeptId.value !==
                    undefined
                ) {
                    params.dept_id =
                        searchDeptId.value;
                }

                // -------------------------------------------------
                // 状态
                // -------------------------------------------------

                if (
                    searchStatus.value
                ) {
                    params.status =
                        searchStatus.value;
                }

                // -------------------------------------------------
                // 创建时间
                // -------------------------------------------------

                if (
                    searchCreatedTime.value
                        .length === 2
                ) {
                    params.created_time =
                        searchCreatedTime.value;
                }

                const response =
                    await UserAPI.listUser(
                        params
                    );

                const result =
                    response.data.data;

                userList.value =
                    result?.items || [];

                total.value =
                    result?.total || 0;

                return userList.value;
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

            await fetchUserList();
        }

        async function setPageSize(
            value: number
        ) {
            pageSize.value =
                value;

            pageNo.value =
                1;

            await fetchUserList();
        }

        // =========================================================
        // 创建
        // =========================================================

        async function createUser(
            form: UserForm
        ) {
            await UserAPI.createUser(
                form
            );

            await fetchUserList();
        }

        // =========================================================
        // 修改
        // =========================================================

        async function updateUser(
            id: number,
            form: UserForm
        ) {
            await UserAPI.updateUser(
                id,
                form
            );

            await fetchUserList();
        }

        // =========================================================
        // 删除
        // =========================================================

        async function deleteUser(
            ids: number[]
        ) {
            await UserAPI.deleteUser(
                ids
            );

            /*
             * 如果删除后当前页没有数据，
             * 自动回到上一页。
             */
            if (
                userList.value.length ===
                    ids.length &&
                pageNo.value > 1
            ) {
                pageNo.value -= 1;
            }

            await fetchUserList();
        }

        // =========================================================
        // 修改状态
        // =========================================================

        async function updateUserStatus(
            ids: number[],
            status: string
        ) {
            await UserAPI.batchUser({
                ids,
                status,
            });

            await fetchUserList();
        }

        // =========================================================
        // 获取详情
        // =========================================================

        async function getUserDetail(
            id: number
        ): Promise<UserInfo | undefined> {  // 添加明确的返回类型
            const response =
                await UserAPI.detailUser(
                    id
                );

            return response.data.data;
        }

        // =========================================================
        // 重置密码
        // =========================================================

        async function resetUserPassword(
            data: ResetPasswordForm
        ) {
            await UserAPI.resetUserPassword(
                data
            );
        }

        // =========================================================
        // 导出
        // =========================================================

        async function exportUser() {
            const params:
                UserPageQuery = {
                page_no:
                    pageNo.value,

                page_size:
                    pageSize.value,
            };

            if (
                searchUsername.value
                    .trim()
            ) {
                params.username =
                    searchUsername.value
                        .trim();
            }

            if (
                searchName.value
                    .trim()
            ) {
                params.name =
                    searchName.value
                        .trim();
            }

            if (
                searchMobile.value
                    .trim()
            ) {
                params.mobile =
                    searchMobile.value
                        .trim();
            }

            if (
                searchEmail.value
                    .trim()
            ) {
                params.email =
                    searchEmail.value
                        .trim();
            }

            if (
                searchDeptId.value !==
                undefined
            ) {
                params.dept_id =
                    searchDeptId.value;
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

            const response =
                await UserAPI.exportUser(
                    params
                );

            return response.data;
        }

       

        // =========================================================
        // 下载导入模板
        // =========================================================

        // 在 store 中
        async function downloadTemplate(): Promise<Blob | undefined> {
            try {
                const response = await UserAPI.downloadTemplateUser();
                // 如果 response.data 是 ApiResponse 但实际内容是 Blob
                if (response.data instanceof Blob) {
                    return response.data;
                }
                // 或者如果数据在 response 中
                if (response instanceof Blob) {
                    return response;
                }
                // 如果 response.data 包含 blob 数据
                if (response.data && typeof response.data === 'object' && 'blob' in response.data) {
                    return response.data.blob as Blob;
                }
                return undefined;
            } catch (error) {
                console.error("下载模板失败:", error);
                throw error;
            }
        }

        // =========================================================
        // 导入用户
        // =========================================================

        async function importUser(
            file: File
        ): Promise<UserImportResult | undefined> {
            const formData =
                new FormData();

            formData.append(
                "file",
                file
            );

            const response = await UserAPI.importUser(formData);
            return response.data.data;
        }

        // =========================================================
        // 搜索
        // =========================================================

        function resetSearch() {
            searchUsername.value =
                "";

            searchName.value =
                "";

            searchMobile.value =
                "";

            searchEmail.value =
                "";

            searchDeptId.value =
                undefined;

            searchStatus.value =
                "";

            searchCreatedTime.value =
                [];

            pageNo.value =
                1;
        }

        async function resetSearchAndFetch() {
            resetSearch();

            await fetchUserList();
        }

        // =========================================================
        // 清理状态
        // =========================================================

        function clearUserManagementState() {
            userList.value =
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
            userList,
            loading,
            total,

            // 分页
            pageNo,
            pageSize,

            // 搜索
            searchUsername,
            searchName,
            searchMobile,
            searchEmail,
            searchDeptId,
            searchStatus,
            searchCreatedTime,

            // 查询
            fetchUserList,

            // 分页
            setPageNo,
            setPageSize,

            // CRUD
            createUser,
            updateUser,
            deleteUser,
            updateUserStatus,
            getUserDetail,

            // 密码
            resetUserPassword,

            // 导出
            exportUser,

            // 导入
            downloadTemplate,
            importUser,

            // 搜索
            resetSearch,
            resetSearchAndFetch,

            // 清理
            clearUserManagementState,
        };
    }
);
