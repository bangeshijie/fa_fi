<template>
    <section class="admin-page">
        <header class="page-heading">
            <div>
                <div class="heading-title-row">
                    <h2>用户管理</h2>
                    <p class="eyebrow">系统用户</p>
                </div>
                <p class="heading-copy">维护登录账号、组织关系和访问身份。</p>
            </div>
            <div class="heading-index">01 / USERS</div>
        </header>

        <!-- ===================================================== -->
        <!-- 搜索 -->
        <!-- ===================================================== -->

        <el-card shadow="never" class="content-card search-card">
            <el-form :inline="true" class="search-bar" @submit.prevent>
                <!-- 用户名 -->
                <el-form-item label="用户名">
                    <el-input v-model="userStore.searchUsername
                        " placeholder="请输入用户名" clearable style="width: 180px" @keyup.enter="
                            handleSearch
                        " />
                </el-form-item>

                <!-- 姓名 -->
                <el-form-item label="姓名">
                    <el-input v-model="userStore.searchName
                        " placeholder="请输入姓名" clearable style="width: 160px" @keyup.enter="
                            handleSearch
                        " />
                </el-form-item>

                <!-- 手机号 -->
                <el-form-item label="手机号">
                    <el-input v-model="userStore.searchMobile
                        " placeholder="请输入手机号" clearable style="width: 180px" @keyup.enter="
                            handleSearch
                        " />
                </el-form-item>

                <!-- 部门 -->
                <el-form-item label="部门">
                    <el-tree-select v-model="userStore.searchDeptId
                        " :data="deptStore.deptTree
                            " node-key="id" clearable check-strictly filterable placeholder="请选择部门"
                        style="width: 180px" :props="{
                            label: 'name',
                            children:
                                'children',
                        }" />
                </el-form-item>

                <!-- 状态 -->
                <el-form-item label="状态">
                    <el-select v-model="userStore.searchStatus
                        " placeholder="请选择状态" clearable style="width: 140px">
                        <el-option label="启用" value="0" />

                        <el-option label="停用" value="1" />
                    </el-select>
                </el-form-item>

                <!-- 创建时间 -->
                <el-form-item label="创建时间">
                    <el-date-picker v-model="userStore.searchCreatedTime
                        " type="datetimerange" range-separator="至" start-placeholder="开始时间" end-placeholder="结束时间"
                        value-format="YYYY-MM-DD HH:mm:ss" clearable />
                </el-form-item>

                <!-- 按钮 -->
                <el-form-item>
                    <el-button type="primary" @click="
                        handleSearch
                    ">
                        查询
                    </el-button>

                    <el-button @click="
                        handleReset
                    ">
                        重置
                    </el-button>
                </el-form-item>
            </el-form>
        </el-card>

        <el-row :gutter="12" class="summary-row">
            <el-col :xs="12" :sm="8">
                <el-card shadow="never" class="summary-card">
                    <span class="summary-label">用户总数</span>
                    <strong>{{ userStore.total }}</strong>
                    <small>当前查询结果</small>
                </el-card>
            </el-col>
            <el-col :xs="12" :sm="8">
                <el-card shadow="never" class="summary-card">
                    <span class="summary-label">当前页正常</span>
                    <strong>{{ pageEnabledCount }}</strong>
                    <small>状态为启用的用户</small>
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
                        <strong>用户列表</strong>
                    </div>
                    <div class="heading-actions">
                        <!-- 新增 -->
                        <el-button type="primary" @click="
                            handleCreate
                        ">
                            新增用户
                        </el-button>

                        <!-- 批量删除 -->
                        <el-button type="danger" :disabled="selectedIds.length ===
                            0
                            " @click="
                                handleBatchDelete
                            ">
                            批量删除
                        </el-button>

                        <!-- 导入 -->
                        <el-button @click="
                            importDialogVisible =
                            true
                            ">
                            导入
                        </el-button>

                        <!-- 导出 -->
                        <el-button @click="
                            handleExport
                        ">
                            导出
                        </el-button>
                    </div>
                </div>
            </template>

            <!-- =================================================== -->
            <!-- 表格 -->
            <!-- =================================================== -->

            <el-table v-loading="userStore.loading
                " :data="userStore.userList
                    " row-key="id" border stripe class="data-table" @selection-change="
                        handleSelectionChange
                    ">
                <!-- 多选 -->
                <el-table-column type="selection" width="55" align="center" />

                <!-- ID -->
                <el-table-column prop="id" label="用户编号" width="90" align="center" />

                <!-- 用户名 -->
                <el-table-column prop="username" label="用户名" min-width="130" />

                <!-- 姓名 -->
                <el-table-column prop="name" label="姓名" min-width="120" />

                <!-- 性别 -->
                <el-table-column label="性别" width="90" align="center">
                    <template #default="{ row }">
                        {{ getDictLabel(sexOptions, row.gender) }}
                    </template>
                </el-table-column>

                <!-- 部门 -->
                <el-table-column label="部门" min-width="140">
                    <template #default="{ row }">
                        {{
                            row.dept?.name ||
                            "-"
                        }}
                    </template>
                </el-table-column>

                <!-- 岗位 -->
                <el-table-column label="岗位" min-width="150">
                    <template #default="{ row }">
                        <el-tag v-for="position in row.positions ||
                            []" :key="position.id" size="small" class="tag-item">
                            {{
                                position.name ||
                                "-"
                            }}
                        </el-tag>

                        <span v-if="
                            !row.positions
                                ?.length
                        ">
                            -
                        </span>
                    </template>
                </el-table-column>

                <!-- 角色 -->
                <el-table-column label="角色" min-width="150">
                    <template #default="{ row }">
                        <el-tag v-for="role in row.roles ||
                            []" :key="role.id" size="small" class="tag-item">
                            {{
                                role.name ||
                                "-"
                            }}
                        </el-tag>

                        <span v-if="
                            !row.roles
                                ?.length
                        ">
                            -
                        </span>
                    </template>
                </el-table-column>

                <!-- 手机 -->
                <el-table-column prop="mobile" label="手机号" min-width="140" />

                <!-- 邮箱 -->
                <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />

                <!-- 状态 -->
                <el-table-column label="状态" width="100" align="center">
                    <template #default="{ row }">
                        <el-switch :model-value="row.status ===
                            '0'
                            " @change="
                                handleStatusChange(
                                    row,
                                    $event
                                )
                                " />
                    </template>
                </el-table-column>

                <!-- 最后登录 -->
                <el-table-column prop="last_login" label="最后登录" width="180" show-overflow-tooltip />

                <!-- 操作 -->
                <el-table-column label="操作" width="250" fixed="right" align="center">
                    <template #default="{ row }">
                        <el-button class="table-action table-action--edit" link type="primary" @click="
                            handleEdit(
                                row
                            )
                            ">
                            编辑
                        </el-button>

                        <el-button class="table-action table-action--reset" link type="warning" @click="
                            handleResetPassword(
                                row
                            )
                            ">
                            重置密码
                        </el-button>

                        <el-button class="table-action table-action--delete" link type="danger" @click="
                            handleDelete(
                                row
                            )
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
                <el-pagination v-model:current-page="userStore.pageNo
                    " v-model:page-size="userStore.pageSize
                        " :total="userStore.total
                            " :page-sizes="[10, 20, 30, 50]
                                " layout="total, sizes, prev, pager, next, jumper" @current-change="
                                    userStore.setPageNo
                                " @size-change="
                                    userStore.setPageSize
                                " />
            </div>
        </el-card>

        <!-- ===================================================== -->
        <!-- 新增 / 编辑用户 -->
        <!-- ===================================================== -->

        <el-dialog v-model="formVisible" :title="formMode === 'create'
            ? '新增用户'
            : '编辑用户'
            " width="650px" destroy-on-close>
            <el-form ref="formRef" :model="form" :rules="formRules" label-width="90px" status-icon>
                <!-- 用户名 -->
                <el-form-item label="用户名" prop="username">
                    <el-input v-model="form.username
                        " maxlength="32" show-word-limit clearable placeholder="请输入用户名" :disabled="formMode ===
                            'edit'
                            " />
                </el-form-item>

                <!-- 密码 -->
                <el-form-item v-if="
                    formMode ===
                    'create'
                " label="密码" prop="password">
                    <el-input v-model="form.password
                        " type="password" maxlength="128" show-password clearable placeholder="请输入登录密码" />
                </el-form-item>

                <!-- 姓名 -->
                <el-form-item label="姓名" prop="name">
                    <el-input v-model="form.name
                        " maxlength="32" clearable placeholder="请输入姓名" />
                </el-form-item>

                <!-- 性别 -->
                <el-form-item label="性别" prop="gender">
                    <el-radio-group v-model="form.gender
                        ">
                        <el-radio
                            v-for="item in sexOptions"
                            :key="item.dict_value"
                            :value="item.dict_value"
                        >
                            {{ item.dict_label }}
                        </el-radio>
                    </el-radio-group>
                </el-form-item>

                <!-- 手机 -->
                <el-form-item label="手机号" prop="mobile">
                    <el-input v-model="form.mobile
                        " maxlength="11" clearable placeholder="请输入手机号" />
                </el-form-item>

                <!-- 邮箱 -->
                <el-form-item label="邮箱" prop="email">
                    <el-input v-model="form.email
                        " maxlength="64" clearable placeholder="请输入邮箱" />
                </el-form-item>

                <!-- 部门 -->
                <el-form-item label="部门" prop="dept_id">
                    <el-tree-select v-model="form.dept_id
                        " :data="deptStore.deptTree
                            " node-key="id" check-strictly filterable clearable placeholder="请选择所属部门"
                        style="width: 100%" :props="{
                            label: 'name',
                            children:
                                'children',
                        }" />
                </el-form-item>

                <!-- 岗位 -->
                <el-form-item label="岗位" prop="position_ids">
                    <el-select v-model="form.position_ids
                        " multiple filterable clearable collapse-tags collapse-tags-tooltip placeholder="请选择岗位"
                        style="width: 100%">
                        <el-option v-for="position in positionStore.positionList" :key="position.id
                            " :label="position.name ||
                                '-'
                                " :value="position.id
                                    " :disabled="position.id ==
                                        null
                                        " />
                    </el-select>
                </el-form-item>

                <!-- 角色 -->
                <el-form-item label="角色" prop="role_ids">
                    <el-select v-model="form.role_ids
                        " multiple filterable clearable collapse-tags collapse-tags-tooltip placeholder="请选择角色"
                        style="width: 100%">
                        <el-option v-for="role in roleStore.roleList" :key="role.id
                            " :label="role.name ||
                                '-'
                                " :value="role.id
                                    " :disabled="role.id ==
                                        null
                                        " />
                    </el-select>
                </el-form-item>

                <!-- 状态 -->
                <el-form-item label="状态" prop="status">
                    <el-switch v-model="statusEnabled
                        " inline-prompt active-text="启用" inactive-text="停用" />
                </el-form-item>

                <!-- 超级管理员 -->
                <el-form-item label="超级管理员" prop="is_superuser">
                    <el-switch v-model="form.is_superuser
                        " inline-prompt active-text="是" inactive-text="否" />
                </el-form-item>

                <!-- 备注 -->
                <el-form-item label="备注" prop="description">
                    <el-input v-model="form.description
                        " type="textarea" :rows="3" maxlength="255" show-word-limit placeholder="请输入备注" />
                </el-form-item>
            </el-form>

            <template #footer>
                <el-button @click="
                    formVisible = false
                    ">
                    取消
                </el-button>

                <el-button type="primary" :loading="formLoading
                    " @click="
                        handleSubmit
                    ">
                    保存
                </el-button>
            </template>
        </el-dialog>

        <!-- ===================================================== -->
        <!-- 重置密码 -->
        <!-- ===================================================== -->

        <el-dialog v-model="resetPasswordVisible
            " title="重置密码" width="450px" destroy-on-close>
            <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="90px" status-icon>
                <el-form-item label="用户名">
                    <el-input :model-value="resetPasswordUser
                        ?.username ||
                        ''
                        " disabled />
                </el-form-item>

                <el-form-item label="新密码" prop="password">
                    <el-input v-model="passwordForm.password" type="password" show-password maxlength="128" clearable
                        placeholder="请输入新密码" />
                </el-form-item>

                <el-form-item label="确认密码" prop="confirmPassword">
                    <el-input v-model="passwordForm.confirmPassword" type="password" show-password maxlength="128"
                        clearable placeholder="请再次输入新密码" />
                </el-form-item>
            </el-form>

            <template #footer>
                <el-button @click="
                    resetPasswordVisible =
                    false
                    ">
                    取消
                </el-button>

                <el-button type="primary" :loading="resetPasswordLoading
                    " @click="
                        handleResetPasswordSubmit
                    ">
                    确定
                </el-button>
            </template>
        </el-dialog>

        <!-- ===================================================== -->
        <!-- 导入 -->
        <!-- ===================================================== -->

        <el-dialog v-model="importDialogVisible
            " title="导入用户" width="500px" destroy-on-close>
            <el-alert title="请先下载模板，按照模板格式填写用户数据后再导入。" type="info" :closable="false" show-icon />

            <div class="import-container">
                <el-button link type="primary" @click="
                    handleDownloadTemplate
                ">
                    下载导入模板
                </el-button>

                <el-upload ref="uploadRef" :auto-upload="false" :limit="1" accept=".xlsx,.xls" :show-file-list="true"
                    :on-change="handleFileChange
                        " :on-remove="handleFileRemove
                            ">
                    <el-button>
                        选择 Excel 文件
                    </el-button>

                    <template #tip>
                        <div class="el-upload__tip">
                            仅支持 .xlsx / .xls 文件
                        </div>
                    </template>
                </el-upload>
            </div>

            <template #footer>
                <el-button @click="
                    importDialogVisible =
                    false
                    ">
                    取消
                </el-button>

                <el-button type="primary" :loading="importLoading
                    " :disabled="!importFile
                        " @click="
                            handleImport
                        ">
                    开始导入
                </el-button>
            </template>
        </el-dialog>

        <!-- ===================================================== -->
        <!-- 导入结果 -->
        <!-- ===================================================== -->

        <el-dialog v-model="importResultVisible
            " title="导入结果" width="760px" destroy-on-close>
            <template v-if="importResult">
                <el-alert :title="importResult.failed_count
                    ? '导入已完成，但有部分数据未成功处理。'
                    : '全部数据已成功处理。'" :type="importResult.failed_count ? 'warning' : 'success'" show-icon
                    :closable="false" />

                <div class="import-result-summary">
                    <div class="import-result-item">
                        <span>数据总数</span>
                        <strong>{{ importResult.total_count }}</strong>
                    </div>
                    <div class="import-result-item import-result-item--success">
                        <span>成功处理</span>
                        <strong>{{ importResult.success_count }}</strong>
                    </div>
                    <div class="import-result-item import-result-item--primary">
                        <span>新增用户</span>
                        <strong>{{ importResult.created_count }}</strong>
                    </div>
                    <div class="import-result-item import-result-item--warning">
                        <span>更新用户</span>
                        <strong>{{ importResult.updated_count }}</strong>
                    </div>
                    <div class="import-result-item import-result-item--warning">
                        <span>重复账号</span>
                        <strong>{{ importResult.duplicate_count }}</strong>
                    </div>
                    <div class="import-result-item import-result-item--danger">
                        <span>失败数据</span>
                        <strong>{{ importResult.failed_count }}</strong>
                    </div>
                </div>

                <div v-if="importResult.errors.length" class="import-error-section">
                    <div class="import-error-heading">
                        <strong>失败明细</strong>
                        <span v-if="importResult.errors_truncated">仅展示前 {{ importResult.errors.length }} 条</span>
                    </div>
                    <el-table :data="importResult.errors" border stripe max-height="360px">
                        <el-table-column prop="row_number" label="Excel 行号" width="110" align="center" />
                        <el-table-column prop="username" label="账号" min-width="160" show-overflow-tooltip />
                        <el-table-column prop="reason" label="失败原因" min-width="300" show-overflow-tooltip />
                    </el-table>
                </div>
            </template>

            <template #footer>
                <el-button @click="importResultVisible = false">关闭</el-button>
                <el-button type="primary" @click="handleImportResultConfirm">刷新用户列表</el-button>
            </template>
        </el-dialog>
    </section>
</template>

<script setup lang="ts">
defineOptions({ name: 'User' })
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
    UploadFile,
    UploadInstance,
} from "element-plus";

import {
    ElMessage,
    ElMessageBox,
} from "element-plus";

import { useUserStore } from "@/store/user";
import { useDeptStore } from "@/store/dept";
import { usePositionStore } from "@/store/position";
import { useRoleStore } from "@/store/role";
import { useDictOptions } from "@/hooks";

import type {
    UserInfo,
    UserForm,
    UserImportResult,
} from "@/api/module_system/user";
import {
    getDefaultDictValue,
    getDictLabel,
    USER_SEX_DICT_TYPE,
} from "@/utils/dict";
import { isHttpError } from "@/utils/request";

// =========================================================
// Store
// =========================================================

const userStore =
    useUserStore();

const deptStore =
    useDeptStore();

const positionStore =
    usePositionStore();

const roleStore =
    useRoleStore();

// =========================================================
// 页面状态
// =========================================================

const selectedIds =
    ref<number[]>([]);

const { options: sexOptions, load: loadSexDictOptions } =
    useDictOptions(USER_SEX_DICT_TYPE);

const pageEnabledCount = computed(() =>
    userStore.userList.filter((item) => item.status === "0").length
);

async function loadSexOptions() {
    try {
        await loadSexDictOptions();
        if (formMode.value === "create" && !form.gender) {
            form.gender = getDefaultDictValue(sexOptions.value) || "";
        }
    } catch (error) {
        console.error("加载性别字典失败", error);
        ElMessage.error("性别选项加载失败，请刷新后重试");
    }
}

// =========================================================
// 搜索
// =========================================================

async function handleSearch() {
    userStore.pageNo =
        1;

    await userStore.fetchUserList();
}

async function handleReset() {
    await userStore.resetSearchAndFetch();
}

// =========================================================
// 表格选择
// =========================================================

function handleSelectionChange(
    rows: UserInfo[]
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
    ref<"create" | "edit">(
        "create"
    );

const formRef =
    ref<FormInstance>();

const editingId =
    ref<number | null>(
        null
    );

const form =
    reactive<UserForm>({
        username: "",
        name: "",
        password: "",
        dept_id: undefined,
        role_ids: [],
        position_ids: [],
        gender: "",
        email: "",
        mobile: "",
        status: "0",
        is_superuser: false,
        description: "",
    });

// =========================================================
// 状态
// =========================================================

const statusEnabled =
    computed({
        get: () =>
            form.status ===
            "0",

        set: value => {
            form.status =
                value
                    ? "0"
                    : "1";
        },
    });

// =========================================================
// 表单校验
// =========================================================

const formRules: FormRules = {
    username: [
        {
            required: true,
            message:
                "请输入用户名",
            trigger: "blur",
        },

        {
            min: 4,
            max: 32,
            message:
                "用户名长度为 4-32 个字符",
            trigger: "blur",
        },

        {
            pattern:
                /^[A-Za-z0-9][A-Za-z0-9_.-]*$/,
            message:
                "用户名必须以字母或数字开头，只能包含字母、数字、下划线、点和横线",
            trigger: "blur",
        },
    ],

    password: [
        {
            required: true,
            message:
                "请输入密码",
            trigger: "blur",
        },

        {
            min: 6,
            max: 128,
            message:
                "密码长度为 6-128 个字符",
            trigger: "blur",
        },
    ],

    name: [
        {
            required: true,
            message:
                "请输入姓名",
            trigger: "blur",
        },

        {
            max: 32,
            message:
                "姓名长度不能超过32个字符",
            trigger: "blur",
        },
    ],

    mobile: [
        {
            pattern:
                /^1[3-9]\d{9}$/,
            message:
                "请输入正确的手机号",
            trigger: "blur",
        },
    ],

    // email必填且验证格式的情况

    // email: [
    //     {
    //         type: "email",
    //         message:
    //             "请输入正确的邮箱地址",
    //         trigger: "blur",
    //     },
    // ],

    email: [
        {
            validator: (_rule: any, value: string | undefined, callback: (error?: Error) => void) => {


                if (value === undefined || value === null || value === '') {

                    callback();
                    return;
                }

                const trimmedValue = String(value).trim();


                if (!trimmedValue) {

                    callback();
                    return;
                }

                const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
                const isValid = emailRegex.test(trimmedValue);


                if (isValid) {
                    callback();
                } else {
                    callback(new Error("请输入正确的邮箱地址"));
                }
            },
            trigger: "blur",
        },
    ],
};

// =========================================================
// 重置表单
// =========================================================

function resetForm() {
    form.username =
        "";

    form.name =
        "";

    form.password =
        "";

    form.dept_id =
        undefined;

    form.role_ids =
        [];

    form.position_ids =
        [];

    form.gender =
        getDefaultDictValue(sexOptions.value) || "";

    form.email =
        "";

    form.mobile =
        "";

    form.status =
        "0";

    form.is_superuser =
        false;

    form.description =
        "";

    nextTick(() => {
        formRef.value?.clearValidate();
    });
}

// =========================================================
// 打开新增
// =========================================================

async function handleCreate() {
    formMode.value =
        "create";

    editingId.value =
        null;

    resetForm();

    await loadSelectorData();

    formVisible.value =
        true;
}

// =========================================================
// 打开编辑
// =========================================================

async function handleEdit(
    row: UserInfo
) {
    if (
        row.id ==
        null
    ) {
        ElMessage.error(
            "用户编号不存在"
        );

        return;
    }

    const detail =
        await userStore.getUserDetail(
            row.id
        );

    if (!detail) {
        return;
    }

    formMode.value =
        "edit";

    editingId.value =
        row.id;

    form.username =
        detail.username ||
        "";

    form.name =
        detail.name ||
        "";

    form.password =
        "";

    form.dept_id =
        detail.dept_id;

    form.role_ids =
        detail.roles
            ?.map(
                role => role.id
            )
            .filter((id): id is number =>
                typeof id === "number"
            ) || [];

    form.position_ids =
        detail.positions
            ?.map(
                position =>
                    position.id
            )
            .filter(
                (
                    id
                ): id is number =>
                    typeof id ===
                    "number"
            ) || [];

    form.gender =
        detail.gender
            ? String(
                detail.gender
            )
            : getDefaultDictValue(sexOptions.value) || "";

    form.email =
        detail.email ||
        "";

    form.mobile =
        detail.mobile ||
        "";

    form.status =
        detail.status ||
        "0";

    form.is_superuser =
        detail.is_superuser ??
        false;

    form.description =
        detail.description ||
        "";

    await loadSelectorData();

    formVisible.value =
        true;

    await nextTick();

    formRef.value?.clearValidate();
}

// =========================================================
// 加载选择器数据
// =========================================================

async function loadSelectorData() {
    await loadSexOptions();

    /*
     * 部门树
     */
    if (
        !deptStore.deptTree.length
    ) {
        await deptStore.fetchDeptTree();
    }

    /*
     * 岗位
     */
    if (
        !positionStore.positionList
            .length
    ) {
        await positionStore.fetchPositionList();
    }

    /*
     * 角色
     */
    if (
        !roleStore.roleList.length
    ) {
        await roleStore.fetchRoleList();
    }
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
        const payload:
            UserForm = {
            username:
                form.username
                    ?.trim(),

            name:
                form.name
                    ?.trim(),

            password:
                formMode.value ===
                    "create"
                    ? form.password
                        ?.trim()
                    : undefined,

            dept_id:
                form.dept_id,

            role_ids:
                form.role_ids ||
                [],

            position_ids:
                form.position_ids ||
                [],

                gender:
                form.gender || getDefaultDictValue(sexOptions.value),

            email:
                form.email
                    ?.trim() || undefined,

            mobile:
                form.mobile
                    ?.trim() || undefined,

            status:
                form.status ||
                "0",

            is_superuser:
                form.is_superuser ??
                false,

            description:
                form.description
                    ?.trim() || undefined,
        };

        if (
            formMode.value ===
            "create"
        ) {
            await userStore.createUser(
                payload
            );

            ElMessage.success(
                "创建成功"
            );
        } else {
            if (
                editingId.value ==
                null
            ) {
                return;
            }

            await userStore.updateUser(
                editingId.value,
                payload
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
    row: UserInfo
) {
    if (
        row.id ==
        null
    ) {
        ElMessage.error(
            "用户编号不存在"
        );

        return;
    }

    await ElMessageBox.confirm(
        `确定要删除用户「${row.username ||
        row.name ||
        row.id
        }」吗？`,
        "删除确认",
        {
            type: "warning",
        }
    );

    await userStore.deleteUser([
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
        selectedIds.value
            .length === 0
    ) {
        return;
    }

    await ElMessageBox.confirm(
        `确定要删除选中的 ${selectedIds.value.length} 个用户吗？`,
        "批量删除",
        {
            type: "warning",
        }
    );

    await userStore.deleteUser(
        selectedIds.value
    );

    selectedIds.value =
        [];

    ElMessage.success(
        "删除成功"
    );
}

// =========================================================
// 状态
// =========================================================

async function handleStatusChange(
    row: UserInfo,
    value:
        | string
        | number
        | boolean
) {
    if (
        row.id ==
        null
    ) {
        return;
    }

    const enabled =
        Boolean(value);

    const status =
        enabled
            ? "0"
            : "1";

    try {
        await userStore.updateUserStatus(
            [row.id],
            status
        );

        ElMessage.success(
            enabled
                ? "已启用"
                : "已停用"
        );
    } catch {
        await userStore.fetchUserList();
    }
}

// =========================================================
// 重置密码
// =========================================================

const resetPasswordVisible =
    ref(false);

const resetPasswordLoading =
    ref(false);

const resetPasswordUser =
    ref<UserInfo | null>(
        null
    );

const passwordFormRef =
    ref<FormInstance>();

const passwordForm =
    reactive({
        password: "",
        confirmPassword:
            "",
    });

const validateConfirmPassword =
    (
        _rule: unknown,
        value: string,
        callback: (
            error?: Error
        ) => void
    ) => {
        if (
            !value
        ) {
            callback(
                new Error(
                    "请再次输入密码"
                )
            );

            return;
        }

        if (
            value !==
            passwordForm.password
        ) {
            callback(
                new Error(
                    "两次输入的密码不一致"
                )
            );

            return;
        }

        callback();
    };

const passwordRules:
    FormRules = {
    password: [
        {
            required: true,
            message:
                "请输入新密码",
            trigger: "blur",
        },

        {
            min: 6,
            max: 128,
            message:
                "密码长度为 6-128 个字符",
            trigger: "blur",
        },
    ],

    confirmPassword: [
        {
            validator:
                validateConfirmPassword,
            trigger: "blur",
        },
    ],
};

function handleResetPassword(
    row: UserInfo
) {
    if (
        row.id ==
        null
    ) {
        ElMessage.error(
            "用户编号不存在"
        );

        return;
    }

    resetPasswordUser.value =
        row;

    passwordForm.password =
        "";

    passwordForm.confirmPassword =
        "";

    resetPasswordVisible.value =
        true;

    nextTick(() => {
        passwordFormRef.value?.clearValidate();
    });
}

async function handleResetPasswordSubmit() {
    if (
        !passwordFormRef.value
    ) {
        return;
    }

    const valid =
        await passwordFormRef.value.validate();

    if (!valid) {
        return;
    }

    if (
        resetPasswordUser.value
            ?.id ==
        null
    ) {
        return;
    }

    resetPasswordLoading.value =
        true;

    try {
        await userStore.resetUserPassword(
            {
                id:
                    resetPasswordUser
                        .value!
                        .id!,
                password:
                    passwordForm
                        .password,
            }
        );

        ElMessage.success(
            "密码重置成功"
        );

        resetPasswordVisible.value =
            false;
    } finally {
        resetPasswordLoading.value =
            false;
    }
}

// =========================================================
// 导出
// =========================================================

async function handleExport() {
    try {
        const blob =
            await userStore.exportUser();

        if (!blob) {
            ElMessage.error(
                "导出文件为空"
            );

            return;
        }

        downloadBlob(
            blob,
            "用户数据.xlsx"
        );

        ElMessage.success(
            "导出成功"
        );
    } catch (error) {
        console.error(
            "导出用户失败:",
            error
        );

        ElMessage.error(
            "导出失败"
        );
    }
}

// =========================================================
// Blob 下载
// =========================================================

function downloadBlob(
    blob: Blob,
    filename: string
) {
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
        filename;

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
}

// =========================================================
// 导入
// =========================================================

const importDialogVisible =
    ref(false);

const importLoading =
    ref(false);

const importResultVisible =
    ref(false);

const importResult =
    ref<UserImportResult | null>(
        null
    );

const importFile =
    ref<File | null>(
        null
    );

const uploadRef =
    ref<UploadInstance>();

function handleFileChange(
    uploadFile: UploadFile
) {
    importFile.value =
        uploadFile.raw ||
        null;
}

function handleFileRemove() {
    importFile.value =
        null;
}

async function handleDownloadTemplate() {
    try {
        const blob =
            await userStore.downloadTemplate();

        if (!blob) {
            ElMessage.error(
                "模板文件为空"
            );

            return;
        }

        downloadBlob(
            blob,
            "用户导入模板.xlsx"
        );

        ElMessage.success(
            "模板下载成功"
        );
    } catch (error) {
        console.error(
            "下载模板失败:",
            error
        );

        ElMessage.error(
            "模板下载失败"
        );
    }
}

async function handleImport() {
    if (
        !importFile.value
    ) {
        ElMessage.warning(
            "请选择 Excel 文件"
        );

        return;
    }

    importLoading.value =
        true;

    try {
        const result = await userStore.importUser(
            importFile.value
        );

        if (!result) {
            throw new Error("导入接口未返回处理结果");
        }

        importResult.value = result;
        importResultVisible.value = true;

        if (result.failed_count) {
            ElMessage.warning(
                "导入完成，但有失败数据"
            );
        } else {
            ElMessage.success(
                "导入成功"
            );
        }

        importDialogVisible.value =
            false;

        importFile.value =
            null;

        uploadRef.value?.clearFiles();

        await userStore.fetchUserList();
    } catch (error) {
        // 全部失败时后端返回 422，但仍携带结构化结果，继续展示失败行明细。
        if (isHttpError(error)) {
            const responseData =
                error.data as ApiResponse<UserImportResult> | undefined;
            const result = responseData?.data;
            if (result) {
                importResult.value = result;
                importResultVisible.value = true;
                importDialogVisible.value = false;
                importFile.value = null;
                uploadRef.value?.clearFiles();
                return;
            }
        }
        console.error("导入用户失败:", error);
        if (!isHttpError(error)) {
            ElMessage.error(
                error instanceof Error ? error.message : "导入失败"
            );
        }
    } finally {
        importLoading.value =
            false;
    }
}

async function handleImportResultConfirm() {
    importResultVisible.value = false;
    await userStore.fetchUserList();
}

// =========================================================
// 初始化
// =========================================================

onMounted(async () => {
    await loadSexOptions();

    /*
     * 用户列表
     */
    await userStore.fetchUserList();

    /*
     * 部门树
     *
     * 搜索区域和新增/编辑用户都会使用。
     */
    await deptStore.fetchDeptTree();

    /*
     * 岗位和角色作为新增/编辑选择器。
     */
    await positionStore.fetchPositionList();

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
    justify-content: flex-end;
    padding-top: 16px;
}

.tag-item {
    margin-right: 4px;
    margin-bottom: 2px;
}

.import-container {
    padding-top: 20px;
}

.import-container .el-upload {
    margin-top: 16px;
}

.import-result-summary {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 10px;
    margin: 18px 0;
}

.import-result-item {
    padding: 12px;
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 6px;
    background: var(--el-fill-color-lighter);
}

.import-result-item span,
.import-result-item strong {
    display: block;
}

.import-result-item span {
    color: var(--app-muted);
    font-size: 12px;
}

.import-result-item strong {
    margin-top: 6px;
    font-size: 22px;
}

.import-result-item--success strong {
    color: var(--el-color-success);
}

.import-result-item--primary strong {
    color: var(--el-color-primary);
}

.import-result-item--warning strong {
    color: var(--el-color-warning);
}

.import-result-item--danger strong {
    color: var(--el-color-danger);
}

.import-error-section {
    margin-top: 16px;
}

.import-error-heading {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
}

.import-error-heading span {
    color: var(--app-muted);
    font-size: 12px;
}

.table-action {
    font-weight: 600;
    opacity: 1 !important;
}

.table-action--edit {
    color: var(--el-color-primary) !important;
}

.table-action--reset {
    color: var(--el-color-warning) !important;
}

.table-action--delete {
    color: var(--el-color-danger) !important;
}

@media (max-width: 760px) {
    .page-heading {
        align-items: flex-start;
        flex-direction: column;
    }

    .heading-actions {
        justify-content: flex-start;
    }

    .import-result-summary {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
</style>
