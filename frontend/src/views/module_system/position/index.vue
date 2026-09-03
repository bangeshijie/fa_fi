<template>
    <section class="admin-page">
        <header class="page-heading">
            <div>
                <p class="eyebrow">组织配置</p>
                <h1>岗位管理</h1>
                <p class="heading-copy">维护岗位名称、显示顺序和启用状态。</p>
            </div>
            <div class="heading-index">03 / POSITIONS</div>
        </header>
        <!-- ===================================================== -->
        <!-- 搜索 -->
        <!-- ===================================================== -->

        <el-card shadow="never" class="content-card search-card">
            <el-form :inline="true" class="search-bar" @submit.prevent>
                <!-- 岗位名称 -->

                <el-form-item label="岗位名称">
                    <el-input v-model="positionStore.searchName" placeholder="请输入岗位名称" clearable style="width: 200px"
                        @keyup.enter="handleSearch" />
                </el-form-item>

                <!-- 状态 -->

                <el-form-item label="状态">
                    <el-select v-model="positionStore.searchStatus" placeholder="请选择状态" clearable style="width: 150px">
                        <el-option label="启用" value="0" />

                        <el-option label="停用" value="1" />
                    </el-select>
                </el-form-item>

                <!-- 创建时间 -->

                <el-form-item label="创建时间">
                    <el-date-picker v-model="positionStore.searchCreatedTime" type="datetimerange" range-separator="至"
                        start-placeholder="开始时间" end-placeholder="结束时间" value-format="YYYY-MM-DD HH:mm:ss" clearable />
                </el-form-item>

                <!-- 更新时间 -->

                <el-form-item label="更新时间">
                    <el-date-picker v-model="positionStore.searchUpdatedTime" type="datetimerange" range-separator="至"
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
                    <span class="summary-label">岗位总数</span>
                    <strong>{{ positionStore.total }}</strong>
                    <small>当前查询结果</small>
                </el-card>
            </el-col>
            <el-col :xs="12" :sm="8">
                <el-card shadow="never" class="summary-card">
                    <span class="summary-label">当前页启用</span>
                    <strong>{{ pageEnabledCount }}</strong>
                    <small>状态为启用的岗位</small>
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
        <!-- 表格 -->
        <!-- ===================================================== -->

        <el-card shadow="never" class="content-card table-card">
            <template #header>
                <div class="toolbar card-heading">
                    <div class="section-title">
                        <span class="section-index">01</span>
                        <strong>岗位列表</strong>
                    </div>
                    <div class="heading-actions">
                        <!-- 新增 -->

                        <el-button type="primary" @click="handleCreate">
                            新增岗位
                        </el-button>

                        <!-- 批量删除 -->

                        <el-button type="danger" :disabled="selectedIds.length === 0
                            " @click="handleBatchDelete">
                            批量删除
                        </el-button>

                        <!-- 导出 -->

                        <el-button type="success" @click="handleExport">
                            导出
                        </el-button>
                    </div>
                </div>
            </template>

            <!-- =================================================== -->
            <!-- 表格 -->
            <!-- =================================================== -->

            <el-table v-loading="positionStore.loading" :data="positionStore.positionList" row-key="id" border stripe class="data-table"
                @selection-change="
                    handleSelectionChange
                ">
                <!-- 多选 -->

                <el-table-column type="selection" width="55" align="center" />

                <!-- 编号 -->

                <el-table-column prop="id" label="岗位编号" width="90" align="center" />

                <!-- 岗位名称 -->

                <el-table-column prop="name" label="岗位名称" min-width="180" />

                <!-- 排序 -->

                <el-table-column prop="order" label="排序" width="90" align="center" />

                <!-- 创建人 -->

                <el-table-column label="创建人" min-width="120">
                    <template #default="{ row }">
                        {{
                            row.created_by?.name ||
                            "-"
                        }}
                    </template>
                </el-table-column>

                <!-- 创建时间 -->

                <el-table-column prop="created_time" label="创建时间" min-width="180" />

                <!-- 更新人 -->

                <el-table-column label="更新人" min-width="120">
                    <template #default="{ row }">
                        {{
                            row.updated_by?.name ||
                            "-"
                        }}
                    </template>
                </el-table-column>

                <!-- 更新时间 -->

                <el-table-column prop="updated_time" label="更新时间" min-width="180" />

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

                <!-- 操作 -->

                <el-table-column label="操作" width="220" fixed="right" align="center">
                    <template #default="{ row }">
                        <el-button link type="primary" @click="
                            handleEdit(row)
                            ">
                            编辑
                        </el-button>

                        <el-button link type="danger" @click="
                            handleDelete(row)
                            ">
                            删除
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>

            <!-- =================================================== -->
            <!-- 分页 -->
            <!-- =================================================== -->

            <div class="pagination-row">
                <el-pagination v-model:current-page="positionStore.pageNo
                    " v-model:page-size="positionStore.pageSize
                        " :total="positionStore.total
                            " :page-sizes="[10, 20, 30, 50]
                            " layout="total, sizes, prev, pager, next, jumper" @current-change="
                            positionStore.setPageNo
                        " @size-change="
                        positionStore.setPageSize
                    " />
            </div>
        </el-card>

        <!-- ===================================================== -->
        <!-- 新增 / 编辑 -->
        <!-- ===================================================== -->

        <el-dialog v-model="formVisible" :title="formMode === 'create'
            ? '新增岗位'
            : '编辑岗位'
            " width="520px" destroy-on-close>
            <el-form ref="formRef" :model="form" :rules="formRules" label-width="90px" status-icon>
                <!-- 岗位名称 -->

                <el-form-item label="岗位名称" prop="name">
                    <el-input v-model="form.name" maxlength="64" show-word-limit clearable placeholder="请输入岗位名称" />
                </el-form-item>

                <!-- 排序 -->

                <el-form-item label="显示排序" prop="order">
                    <el-input-number v-model="form.order" :min="1" :max="999999" controls-position="right"
                        style="width: 100%" />
                </el-form-item>
            </el-form>

            <template #footer>
                <el-button @click="
                    formVisible = false
                    ">
                    取消
                </el-button>

                <el-button type="primary" :loading="formLoading" @click="handleSubmit">
                    保存
                </el-button>
            </template>
        </el-dialog>
    </section>
</template>

<script setup lang="ts">
defineOptions({ name: 'Position' })
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

import { usePositionStore } from "@/store/position";

import type {
    PositionForm,
    PositionTable,
} from "@/api/module_system/position";

// =========================================================
// Store
// =========================================================

const positionStore =
    usePositionStore();

// =========================================================
// 页面状态
// =========================================================

const selectedIds =
    ref<number[]>([]);

const pageEnabledCount = computed(
    () =>
        positionStore.positionList.filter(
            (item) => item.status === "0"
        ).length
);

// =========================================================
// 搜索
// =========================================================

async function handleSearch() {
    positionStore.pageNo =
        1;

    await positionStore.fetchPositionList();
}

async function handleReset() {
    await positionStore.resetSearchAndFetch();
}

// =========================================================
// 表格选择
// =========================================================

function handleSelectionChange(
    rows: PositionTable[]
) {
    selectedIds.value =
        rows
            .map(
                item =>
                    item.id
            )
            .filter(
                (
                    id
                ): id is number =>
                    typeof id ===
                    "number"
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
    ref<
        "create" | "edit"
    >("create");

const formRef =
    ref<FormInstance>();

const editingId =
    ref<number | null>(
        null
    );

const form =
    reactive<PositionForm>({
        name: "",
        order: 1,
    });

// =========================================================
// 表单校验
// =========================================================

const formRules: FormRules = {
    name: [
        {
            required: true,
            message:
                "请输入岗位名称",
            trigger: "blur",
        },

        {
            min: 1,
            max: 64,
            message:
                "岗位名称长度为 1-64 个字符",
            trigger: "blur",
        },
    ],

    order: [
        {
            required: true,
            message:
                "请输入显示排序",
            trigger: "change",
        },
    ],
};

// =========================================================
// 新增
// =========================================================

function handleCreate() {
    formMode.value =
        "create";

    editingId.value =
        null;

    form.name =
        "";

    form.order =
        1;

    formVisible.value =
        true;

    nextTick(() => {
        formRef.value?.clearValidate();
    });
}

// =========================================================
// 编辑
// =========================================================

async function handleEdit(
    row: PositionTable
) {
    const detail =
        await positionStore.getPositionDetail(
            row.id
        );

    formMode.value =
        "edit";

    editingId.value =
        row.id;

    form.name =
        detail?.name || "";

    form.order =
        detail?.order ?? 1;

    formVisible.value =
        true;

    await nextTick();

    formRef.value?.clearValidate();
}

// =========================================================
// 提交
// =========================================================

async function handleSubmit() {
    if (
        !formRef.value
    ) {
        return;
    }

    const valid =
        await formRef.value.validate();

    if (!valid) {
        return;
    }

    formLoading.value =
        true;

    try {
        const data: PositionForm = {
            name:
                form.name?.trim(),

            order:
                form.order ?? 1,
        };

        if (
            formMode.value ===
            "create"
        ) {
            await positionStore.createPosition(
                data
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

            await positionStore.updatePosition(
                editingId.value,
                data
            );

            ElMessage.success(
                "修改成功"
            );
        }

        formVisible.value =
            false;
    } finally {
        formLoading.value =
            false;
    }
}

// =========================================================
// 删除
// =========================================================

async function handleDelete(
    row: PositionTable
) {
    try {
        await ElMessageBox.confirm(
            `确定要删除岗位「${row.name}」吗？`,
            "删除确认",
            {
                type: "warning",
            }
        );

        await positionStore.deletePosition(
            [row.id]
        );

        ElMessage.success(
            "删除成功"
        );
    } catch (error) {
        /*
         * 用户点击取消时，
         * 不需要提示错误。
         */
        if (
            error ===
            "cancel"
        ) {
            return;
        }

        if (
            error ===
            "close"
        ) {
            return;
        }

        throw error;
    }
}

// =========================================================
// 批量删除
// =========================================================

async function handleBatchDelete() {
    if (
        selectedIds.value
            .length === 0
    ) {
        return;
    }

    try {
        await ElMessageBox.confirm(
            `确定要删除选中的 ${selectedIds.value.length} 个岗位吗？`,
            "批量删除",
            {
                type: "warning",
            }
        );

        await positionStore.deletePosition(
            selectedIds.value
        );

        selectedIds.value =
            [];

        ElMessage.success(
            "删除成功"
        );
    } catch (error) {
        if (
            error ===
            "cancel"
        ) {
            return;
        }

        if (
            error ===
            "close"
        ) {
            return;
        }

        throw error;
    }
}

// =========================================================
// 状态
// =========================================================

async function handleStatusChange(
    row: PositionTable,
    value:
        | string
        | number
        | boolean
) {
    const enabled =
        Boolean(value);

    const status =
        enabled
            ? "0"
            : "1";

    try {
        await positionStore.updatePositionStatus(
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
         * 请求失败重新加载，
         * 恢复真实状态。
         */
        await positionStore.fetchPositionList();
    }
}

// =========================================================
// 导出
// =========================================================

async function handleExport() {
    try {
        const blob =
            await positionStore.exportPosition();

        const url =
            window.URL.createObjectURL(
                blob
            );

        const link =
            document.createElement(
                "a"
            );

        link.href =
            url;

        link.download =
            `岗位列表_${Date.now()}.xlsx`;

        document.body.appendChild(
            link
        );

        link.click();

        document.body.removeChild(
            link
        );

        window.URL.revokeObjectURL(
            url
        );

        ElMessage.success(
            "导出成功"
        );
    } catch (error) {
        console.error(
            "岗位导出失败:",
            error
        );

        ElMessage.error(
            "导出失败"
        );
    }
}

// =========================================================
// 初始化
// =========================================================

onMounted(async () => {
    await positionStore.fetchPositionList();
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

h1 {
    margin: 8px 0 0;
    font-size: clamp(28px, 4vw, 46px);
    letter-spacing: -.045em;
    line-height: 1;
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
