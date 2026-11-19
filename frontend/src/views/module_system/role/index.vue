<template>
    <section class="admin-page">
        <header class="page-heading">
            <div>
                <div class="heading-title-row">
                    <h2>角色管理</h2>
                    <p class="eyebrow">系统权限</p>
                </div>
                <p class="heading-copy">维护角色身份、数据范围和菜单访问权限。</p>
            </div>
            <div class="heading-index">02 / ROLES</div>
        </header>
        <!-- ===================================================== -->
        <!-- 搜索 -->
        <!-- ===================================================== -->

        <el-card shadow="never" class="content-card search-card">
            <el-form :inline="true" class="search-bar" @submit.prevent>
                <!-- 角色名称 -->
                <el-form-item label="角色名称">
                    <el-input v-model="roleStore.searchName" placeholder="请输入角色名称" clearable style="width: 200px"
                        @keyup.enter="handleSearch" />
                </el-form-item>

                <!-- 状态 -->
                <el-form-item label="状态">
                    <el-select v-model="roleStore.searchStatus" placeholder="请选择状态" clearable style="width: 150px">
                        <el-option label="启用" value="0" />

                        <el-option label="停用" value="1" />
                    </el-select>
                </el-form-item>

                <!-- 创建时间 -->
                <el-form-item label="创建时间">
                    <el-date-picker v-model="roleStore.searchCreatedTime" type="datetimerange" range-separator="至"
                        start-placeholder="开始时间" end-placeholder="结束时间" value-format="YYYY-MM-DD HH:mm:ss" clearable />
                </el-form-item>

                <!-- 按钮 -->
                <el-form-item>
                    <el-button type="primary" @click="handleSearch">
                        查询
                    </el-button>

                    <el-button @click="handleReset">
                        重置
                    </el-button>
                </el-form-item>
            </el-form>
        </el-card>

        <el-row :gutter="12" class="summary-row">
            <el-col :xs="12" :sm="8">
                <el-card shadow="never" class="summary-card">
                    <span class="summary-label">角色总数</span>
                    <strong>{{ roleStore.total }}</strong>
                    <small>当前查询结果</small>
                </el-card>
            </el-col>
            <el-col :xs="12" :sm="8">
                <el-card shadow="never" class="summary-card">
                    <span class="summary-label">当前页启用</span>
                    <strong>{{ pageEnabledCount }}</strong>
                    <small>状态为启用的角色</small>
                </el-card>
            </el-col>
            <el-col :xs="12" :sm="8">
                <el-card shadow="never" class="summary-card">
                    <span class="summary-label">已选记录</span>
                    <strong>{{ selectedIds.length }}</strong>
                    <small>可批量删除</small>
                </el-card>
            </el-col>
        </el-row>

        <!-- ===================================================== -->
        <!-- 工具栏 -->
        <!-- ===================================================== -->

        <el-card shadow="never" class="content-card table-card">
            <template #header>
                <div class="toolbar card-heading">
                    <div class="section-title">
                        <span class="section-index">01</span>
                        <strong>角色列表</strong>
                    </div>
                    <div class="heading-actions">
                        <el-button type="primary" @click="handleCreate">
                            新增角色
                        </el-button>

                        <el-button type="danger" :disabled="selectedIds.length === 0
                            " @click="handleBatchDelete">
                            批量删除
                        </el-button>
                    </div>
                </div>
            </template>

            <!-- =================================================== -->
            <!-- 表格 -->
            <!-- =================================================== -->

            <el-table v-loading="roleStore.loading" :data="roleStore.roleList" row-key="id" border stripe class="data-table"
                @selection-change="handleSelectionChange">
                <!-- 多选 -->
                <el-table-column type="selection" width="55" align="center" />

                <!-- ID -->
                <el-table-column prop="id" label="角色编号" width="90" align="center" />

                <!-- 名称 -->
                <el-table-column prop="name" label="角色名称" min-width="150" />

                <!-- 编码 -->
                <el-table-column prop="code" label="角色编码" min-width="150" />

                <!-- 排序 -->
                <el-table-column prop="order" label="排序" width="90" align="center" />

                <!-- 数据权限 -->
                <el-table-column label="数据权限" min-width="160">
                    <template #default="{ row }">
                        {{ getDataScopeLabel(row.data_scope) }}
                    </template>
                </el-table-column>

                <!-- 状态 -->
                <el-table-column label="状态" width="100" align="center">
                    <template #default="{ row }">
                        <el-switch :model-value="row.status === '0'
                            " @change="
                                handleStatusChange(
                                    row,
                                    $event
                                )
                                " />
                    </template>
                </el-table-column>

                <!-- 描述 -->
                <el-table-column prop="description" label="备注" min-width="180" show-overflow-tooltip />

                <!-- 操作 -->
                <el-table-column label="操作" width="280" fixed="right" align="center">
                    <template #default="{ row }">
                        <el-button link type="primary" @click="handlePermission(row)">
                            权限
                        </el-button>

                        <el-button link type="primary" @click="handleEdit(row)">
                            编辑
                        </el-button>

                        <el-button link type="danger" @click="handleDelete(row)">
                            删除
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>

            <!-- =================================================== -->
            <!-- 分页 -->
            <!-- =================================================== -->

            <div class="pagination-row">
                <el-pagination v-model:current-page="roleStore.pageNo
                    " v-model:page-size="roleStore.pageSize
                        " :total="roleStore.total" :page-sizes="[10, 20, 30, 50]"
                    layout="total, sizes, prev, pager, next, jumper" @current-change="
                        roleStore.setPageNo
                    " @size-change="
                        roleStore.setPageSize
                    " />
            </div>
        </el-card>

        <!-- ===================================================== -->
        <!-- 角色新增 / 编辑 -->
        <!-- ===================================================== -->

        <el-dialog v-model="formVisible" :title="formMode === 'create'
            ? '新增角色'
            : '编辑角色'
            " width="520px" destroy-on-close>
            <el-form ref="formRef" :model="form" :rules="formRules" label-width="90px">
                <el-form-item label="角色名称" prop="name">
                    <el-input v-model="form.name" placeholder="请输入角色名称" />
                </el-form-item>

                <el-form-item label="角色编码" prop="code">
                    <el-input v-model="form.code" placeholder="请输入角色编码" />
                </el-form-item>

                <el-form-item label="显示排序" prop="order">
                    <el-input-number v-model="form.order" :min="1" style="width: 100%" />
                </el-form-item>

                <el-form-item label="状态" prop="status">
                    <el-radio-group v-model="form.status">
                        <el-radio value="0">
                            启用
                        </el-radio>

                        <el-radio value="1">
                            停用
                        </el-radio>
                    </el-radio-group>
                </el-form-item>

                <el-form-item label="备注" prop="description">
                    <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入备注" />
                </el-form-item>
            </el-form>

            <template #footer>
                <el-button @click="formVisible = false">
                    取消
                </el-button>

                <el-button type="primary" :loading="formLoading" @click="handleSubmit">
                    确定
                </el-button>
            </template>
        </el-dialog>

        <!-- ===================================================== -->
        <!-- 权限设置 -->
        <!-- ===================================================== -->

        <el-dialog v-model="permissionVisible" title="角色权限设置" width="900px" destroy-on-close>
            <div v-if="
                roleStore.permissionRole
            " class="permission-container">
                <!-- ================================================= -->
                <!-- 数据权限 -->
                <!-- ================================================= -->

                <el-card shadow="never" class="permission-card">
                    <template #header>
                        数据权限
                    </template>

                    <el-radio-group v-model="roleStore.permissionDataScope
                        " @change="
                            roleStore.setPermissionDataScope
                        ">
                        <el-radio :value="1">
                            仅本人
                        </el-radio>

                        <el-radio :value="2">
                            本部门
                        </el-radio>

                        <el-radio :value="3">
                            本部门及以下
                        </el-radio>

                        <el-radio :value="4">
                            全部
                        </el-radio>

                        <el-radio :value="5">
                            自定义部门
                        </el-radio>
                    </el-radio-group>
                    <p class="scope-hint">
                        自定义部门表示只允许访问所选部门的数据；至少选择一个部门。
                    </p>
                </el-card>

                <!-- ================================================= -->
                <!-- 菜单权限 -->
                <!-- ================================================= -->

                <el-card shadow="never" class="permission-card">
                    <template #header>
                        菜单权限
                    </template>

                    <el-tree ref="menuTreeRef" :data="menuStore.menuTree" node-key="id" show-checkbox default-expand-all
                        :props="{
                            label: 'name',
                            children: 'children',
                        }" @check="
                            handleMenuCheck
                        " />
                </el-card>

                <!-- ================================================= -->
                <!-- 部门权限 -->
                <!-- ================================================= -->

                <el-card v-if="
                    roleStore.permissionDataScope ===
                    5
                " shadow="never" class="permission-card">
                    <template #header>
                        自定义部门权限
                    </template>

                    <el-tree ref="deptTreeRef" :data="deptStore.deptTree" node-key="id" show-checkbox default-expand-all
                        :props="{
                            label: 'name',
                            children: 'children',
                        }" @check="
                            handleDeptCheck
                        " />
                </el-card>
            </div>

            <template #footer>
                <el-button @click="
                    permissionVisible = false
                    ">
                    取消
                </el-button>

                <el-button type="primary" :loading="roleStore.permissionLoading
                    " @click="handlePermissionSubmit">
                    保存
                </el-button>
            </template>
        </el-dialog>
    </section>
</template>

<script setup lang="ts">
defineOptions({ name: 'Role' })
import {
    computed,
    nextTick,
    onMounted,
    reactive,
    ref,
} from "vue";

import type {
    FormInstance,
    FormRules,
} from "element-plus";


import {
    ElMessage,
    ElMessageBox,
} from "element-plus";

import { useRoleStore } from "@/store/role";
import { useMenuStore } from "@/store/menu";
import { useDeptStore } from "@/store/dept";
import type {
    RoleForm,
    RoleTable,
} from "@/api/module_system/role";
import type { MenuTable } from "@/api/module_system/menu";

// =========================================================
// Store
// =========================================================

const roleStore =
    useRoleStore();

const menuStore =
    useMenuStore();

const deptStore =
    useDeptStore();

// =========================================================
// 页面状态
// =========================================================

const selectedIds =
    ref<number[]>([]);

const pageEnabledCount = computed(
    () =>
        roleStore.roleList.filter(
            (item) => item.status === "0"
        ).length
);

// =========================================================
// 搜索
// =========================================================

async function handleSearch() {
    roleStore.pageNo = 1;

    await roleStore.fetchRoleList();
}

async function handleReset() {
    await roleStore.resetSearchAndFetch();
}

// =========================================================
// 表格选择
// =========================================================

function handleSelectionChange(
    rows: RoleTable[]
) {
    selectedIds.value =
        rows
            .map((item) => item.id)
            .filter(
                (id): id is number =>
                    typeof id === "number"
            );
}

// =========================================================
// 新增 / 编辑
// =========================================================

const formVisible =
    ref(false);

const formLoading =
    ref(false);

const formMode =
    ref<"create" | "edit">(
        "create"
    );

const formRef =
    ref<FormInstance>();

const editingId =
    ref<number | null>(null);

const form =
    reactive<RoleForm>({
        name: "",
        code: "",
        order: 1,
        status: "0",
        description: "",
    });

const formRules: FormRules = {
    name: [
        {
            required: true,
            message: "请输入角色名称",
            trigger: "blur",
        },
    ],

    code: [
        {
            required: true,
            message: "请输入角色编码",
            trigger: "blur",
        },
    ],

    order: [
        {
            required: true,
            message: "请输入显示排序",
            trigger: "change",
        },
    ],
};

// =========================================================
// 打开新增
// =========================================================

function handleCreate() {
    formMode.value = "create";

    editingId.value = null;

    form.name = "";
    form.code = "";
    form.order = 1;
    form.status = "0";
    form.description = "";

    formVisible.value = true;
}

// =========================================================
// 打开编辑
// =========================================================

async function handleEdit(
    row: RoleTable
) {
    const detail =
        await roleStore.getRoleDetail(
            row.id
        );

    formMode.value = "edit";

    editingId.value = row.id;

    form.name =
        detail.name || "";

    form.code =
        detail.code || "";

    form.order =
        detail.order ?? 1;

    form.status =
        detail.status ?? "0";

    form.description =
        detail.description || "";

    formVisible.value = true;

    await nextTick();

    formRef.value?.clearValidate();
}

// =========================================================
// 提交
// =========================================================

async function handleSubmit() {
    if (!formRef.value) {
        return;
    }

    const valid =
        await formRef.value.validate();

    if (!valid) {
        return;
    }

    formLoading.value = true;

    try {
        if (
            formMode.value ===
            "create"
        ) {
            await roleStore.createRole(
                form
            );

            ElMessage.success(
                "创建成功"
            );
        } else {
            if (
                editingId.value ===
                null
            ) {
                return;
            }

            await roleStore.updateRole(
                editingId.value,
                form
            );

            ElMessage.success(
                "修改成功"
            );
        }

        formVisible.value = false;
    } finally {
        formLoading.value = false;
    }
}

// =========================================================
// 删除
// =========================================================

async function handleDelete(
    row: RoleTable
) {
    await ElMessageBox.confirm(
        `确定要删除角色「${row.name}」吗？`,
        "删除确认",
        {
            type: "warning",
        }
    );

    await roleStore.deleteRole([
        row.id,
    ]);

    ElMessage.success(
        "删除成功"
    );
}

// =========================================================
// 批量删除
// =========================================================

async function handleBatchDelete() {
    if (
        selectedIds.value.length ===
        0
    ) {
        return;
    }

    await ElMessageBox.confirm(
        `确定要删除选中的 ${selectedIds.value.length} 个角色吗？`,
        "批量删除",
        {
            type: "warning",
        }
    );

    await roleStore.deleteRole(
        selectedIds.value
    );

    selectedIds.value = [];

    ElMessage.success(
        "删除成功"
    );
}

// =========================================================
// 状态
// =========================================================

async function handleStatusChange(
    row: RoleTable,
    value: string | number | boolean
) {
    const enabled =
        Boolean(value);

    const status =
        enabled ? "0" : "1";

    try {
        await roleStore.updateRoleStatus(
            [row.id],
            status
        );

        ElMessage.success(
            enabled
                ? "已启用"
                : "已停用"
        );
    } catch {
        /*
         * 请求失败时重新加载，
         * 恢复真实状态。
         */
        await roleStore.fetchRoleList();
    }
}

// =========================================================
// 权限设置
// =========================================================

const permissionVisible =
    ref(false);

const menuTreeRef = ref();
const deptTreeRef = ref();
async function handlePermission(
    row: RoleTable
) {
    /*
     * 先获取最新角色详情。
     *
     * 因为角色列表中的 menus / depts
     * 不一定始终是最新数据。
     */
    const detail =
        await roleStore.getRoleDetail(
            row.id
        );

    roleStore.initPermission(
        detail
    );

    /*
     * 加载菜单树
     */
    await menuStore.fetchMenuTree();

    /*
     * 加载部门树
     */
    await deptStore.fetchDeptTree();

    permissionVisible.value =
        true;

    await nextTick();

    // 设置菜单选中状态
    menuTreeRef.value?.setCheckedKeys(
        getMenuTreeCheckKeys(
            roleStore.permissionMenuIds,
        )
    );

    // 设置部门选中状态
    if (
        roleStore.permissionDataScope ===
        5
    ) {
        deptTreeRef.value?.setCheckedKeys(
            roleStore.permissionDeptIds
        );
    }
}

/**
 * 生成权限树的显示选中项。
 *
 * 角色可以只勾选页面下的一部分按钮权限。此时数据库中仍会保存
 * 页面/目录父级，但不能直接把父级传给 setCheckedKeys，否则 Element Plus
 * 会把父级的全部子节点重新勾选。只传叶子节点（或完整选中的父级），
 * 可以正确还原“全选 / 半选 / 未选”状态。
 */
function getMenuTreeCheckKeys(
    selectedIds: number[],
): number[] {
    const selected = new Set(selectedIds);
    const displayKeys = new Set<number>();

    function getDescendantIds(
        node: MenuTable,
    ): number[] {
        const children = node.children ?? [];
        return children.flatMap((child) => [
            child.id,
            ...getDescendantIds(child),
        ]);
    }

    function visit(node: MenuTable) {
        const children = node.children ?? [];

        if (children.length === 0) {
            if (selected.has(node.id)) {
                displayKeys.add(node.id);
            }
            return;
        }

        const descendantIds = getDescendantIds(node);
        const fullySelected =
            selected.has(node.id) &&
            descendantIds.length > 0 &&
            descendantIds.every((id) => selected.has(id));

        if (fullySelected) {
            displayKeys.add(node.id);
            return;
        }

        children.forEach(visit);
    }

    menuStore.menuTree.forEach(visit);
    return Array.from(displayKeys);
}

// =========================================================
// 菜单选择
// =========================================================

function handleMenuCheck() {
    if (!menuTreeRef.value) {
        return;
    }

    /*
     * 只提交明确勾选的节点。
     *
     * 半选父级代表“只授予部分按钮权限”，
     * 页面和目录父级由后端在生成用户菜单时自动补齐。
     */
    const checkedKeys =
        menuTreeRef.value.getCheckedKeys(false) as number[];
    const halfCheckedKeys =
        (menuTreeRef.value.getHalfCheckedKeys?.() ?? []) as number[];
    const keys = Array.from(
        new Set([
            ...checkedKeys,
            ...halfCheckedKeys,
        ]),
    );

    roleStore.setPermissionMenuIds(
        keys
    );
}

// =========================================================
// 部门选择
// =========================================================

function handleDeptCheck() {
    if (!deptTreeRef.value) {
        return;
    }

    const keys =
        deptTreeRef.value.getCheckedKeys(
            false
        ) as number[];

    roleStore.setPermissionDeptIds(
        keys
    );
}

// =========================================================
// 保存权限
// =========================================================

async function handlePermissionSubmit() {
    await roleStore.savePermission();

    ElMessage.success(
        "权限保存成功"
    );

    permissionVisible.value =
        false;

    roleStore.clearPermissionState();
}

// =========================================================
// 数据权限文字
// =========================================================

function getDataScopeLabel(
    value?: number
) {
    switch (value) {
        case 1:
            return "仅本人";

        case 2:
            return "本部门";

        case 3:
            return "本部门及以下";

        case 4:
            return "全部";

        case 5:
            return "自定义";

        default:
            return "-";
    }
}

// =========================================================
// 初始化
// =========================================================

onMounted(async () => {
    await roleStore.fetchRoleList();
});
</script>

<style scoped>
.admin-page {
    min-height: 100%;
    padding: 14px 4px 36px;
    color: var(--app-text);
}

.page-heading,
.card-heading,
.heading-actions,
.pagination-row {
    display: flex;
    align-items: center;
}

.page-heading {
    justify-content: space-between;
    gap: 24px;
    padding: 6px 0 24px;
    border-bottom: 1px solid var(--app-border);
}

.eyebrow,
.section-index {
    margin: 0;
    color: var(--el-color-primary);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .12em;
}

.heading-copy {
    margin: 12px 0 0;
    color: var(--app-muted);
    font-size: 13px;
}

.heading-index {
    color: var(--app-muted);
    font-family: var(--app-mono);
    font-size: 12px;
    letter-spacing: .08em;
}

.content-card {
    border-color: var(--app-border);
}

.search-card {
    margin-top: 16px;
}

.search-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 0 12px;
}

.summary-row {
    margin: 16px 0;
}

.summary-card {
    min-height: 112px;
}

.summary-label,
.summary-card small {
    display: block;
    color: var(--app-muted);
}

.summary-label {
    font-size: 12px;
}

.summary-card strong {
    display: block;
    margin: 8px 0 4px;
    color: var(--el-color-primary);
    font-size: 30px;
    line-height: 1;
}

.summary-card small {
    font-size: 11px;
}

.table-card {
    margin-top: 16px;
}

.card-heading {
    justify-content: space-between;
    gap: 16px;
}

.section-title {
    display: flex;
    align-items: center;
    gap: 10px;
}

.heading-actions {
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 8px;
}

.data-table {
    width: 100%;
}

.pagination-row {
    display: flex;
    justify-content: flex-end;
    padding-top: 16px;
}

.permission-container {
    max-height: 600px;
    overflow-y: auto;
}

.permission-card {
    margin-bottom: 16px;
}

.scope-hint {
    margin: 10px 0 0;
    color: var(--app-muted);
    font-size: 12px;
}

.permission-card:last-child {
    margin-bottom: 0;
}

@media (max-width: 760px) {
    .page-heading {
        align-items: flex-start;
        flex-direction: column;
    }

    .heading-actions {
        justify-content: flex-start;
    }
}
</style>
