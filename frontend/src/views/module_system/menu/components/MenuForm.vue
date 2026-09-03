<template>
    <el-dialog v-model="visible" :title="dialogTitle" width="720px" destroy-on-close @closed="handleClosed">
        <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" label-position="right">
            <!-- ================================================= -->
            <!-- 基础信息 -->
            <!-- ================================================= -->

            <el-divider content-position="left">
                基础信息
            </el-divider>

            <el-row :gutter="20">
                <!-- 菜单名称 -->
                <el-col :span="12">
                    <el-form-item label="菜单名称" prop="name">
                        <el-input v-model="form.name" maxlength="50" show-word-limit placeholder="请输入菜单名称" />
                    </el-form-item>
                </el-col>

                <!-- 类型 -->
                <el-col :span="12">
                    <el-form-item label="菜单类型" prop="type">
                        <el-select v-model="form.type" style="width: 100%" @change="handleTypeChange">
                            <el-option label="目录" :value="1" />

                            <el-option label="菜单" :value="2" />

                            <el-option label="权限" :value="3" />

                            <el-option label="外链" :value="4" />
                        </el-select>
                    </el-form-item>
                </el-col>

                <!-- 父菜单 -->
                <el-col :span="12">
                    <el-form-item label="父菜单" prop="parent_id">
                        <el-tree-select v-model="form.parent_id" :data="parentOptions" node-key="id" check-strictly
                            clearable filterable default-expand-all :props="{
                                label: 'name',
                                children: 'children',
                            }" placeholder="请选择父菜单" style="width: 100%" />
                    </el-form-item>
                </el-col>

                <!-- 排序 -->
                <el-col :span="12">
                    <el-form-item label="显示排序" prop="order">
                        <el-input-number v-model="form.order" :min="1" :max="99999" controls-position="right"
                            style="width: 100%" />
                    </el-form-item>
                </el-col>

                <!-- 图标 -->
                <el-col :span="12">
                    <el-form-item label="菜单图标" prop="icon">
                        <IconSelect v-model="form.icon" />
                    </el-form-item>
                </el-col>

                <!-- 权限标识 -->
                <el-col :span="12" v-if="showPermission">
                    <el-form-item label="权限标识" prop="permission">
                        <el-input v-model="form.permission" maxlength="100" placeholder="例如：module_system:user:query" />
                    </el-form-item>
                </el-col>

                <!-- 终端 -->
                <el-col :span="12">
                    <el-form-item label="终端" prop="client">
                        <el-radio-group v-model="form.client">
                            <el-radio value="pc">
                                PC端
                            </el-radio>

                            <el-radio value="app">
                                APP端
                            </el-radio>
                        </el-radio-group>
                    </el-form-item>
                </el-col>

                <!-- 状态 -->
                <el-col :span="12">
                    <el-form-item label="状态" prop="status">
                        <el-radio-group v-model="form.status">
                            <el-radio value="0">
                                启用
                            </el-radio>

                            <el-radio value="1">
                                禁用
                            </el-radio>
                        </el-radio-group>
                    </el-form-item>
                </el-col>
            </el-row>

            <!-- ================================================= -->
            <!-- 路由信息 -->
            <!-- ================================================= -->

            <template v-if="showRouteConfig">
                <el-divider content-position="left">
                    路由信息
                </el-divider>

                <el-row :gutter="20">
                    <!-- 路由名称 -->
                    <el-col :span="12">
                        <el-form-item label="路由名称" prop="route_name">
                            <el-input v-model="form.route_name" maxlength="100" placeholder="例如：User" />
                        </el-form-item>
                    </el-col>

                    <!-- 路由地址 -->
                    <el-col :span="12">
                        <el-form-item label="路由地址" prop="route_path">
                            <el-input v-model="form.route_path" maxlength="200" placeholder="例如：/system/user" />
                            <div class="form-tip">
                                路由地址必须以 / 开头
                            </div>
                        </el-form-item>
                    </el-col>

                    <!-- 组件路径 -->
                    <el-col :span="24" v-if="form.type === 2">
                        <el-form-item label="组件路径" prop="component_path">
                            <el-input v-model="form.component_path" maxlength="255"
                                placeholder="例如：module_system/user/index" />

                            <div class="form-tip">
                                对应 src/views 下的 Vue 文件，不要以 / 开头
                            </div>
                        </el-form-item>
                    </el-col>

                    <!-- 重定向 -->
                    <el-col :span="24" v-if="form.type === 1">
                        <el-form-item label="重定向地址" prop="redirect">
                            <el-input v-model="form.redirect" maxlength="200" placeholder="例如：/system/user" />
                        </el-form-item>
                    </el-col>
                </el-row>
            </template>

            <!-- ================================================= -->
            <!-- 外链 -->
            <!-- ================================================= -->

            <template v-if="form.type === 4">
                <el-divider content-position="left">
                    外链配置
                </el-divider>

                <el-form-item label="外链地址" prop="route_path">
                    <el-input v-model="form.route_path" maxlength="200" placeholder="例如：https://www.example.com" />
                </el-form-item>
            </template>

            <!-- ================================================= -->
            <!-- 路由选项 -->
            <!-- ================================================= -->

            <template v-if="showRouteOptions">
                <el-divider content-position="left">
                    路由选项
                </el-divider>

                <el-row :gutter="20">
                    <el-col :span="8">
                        <el-form-item label="缓存页面">
                            <el-switch v-model="form.keep_alive" active-text="是" inactive-text="否" />
                        </el-form-item>
                    </el-col>

                    <el-col :span="8">
                        <el-form-item label="隐藏菜单">
                            <el-switch v-model="form.hidden" active-text="是" inactive-text="否" />
                        </el-form-item>
                    </el-col>

                    <el-col :span="8">
                        <el-form-item label="始终显示">
                            <el-switch v-model="form.always_show" active-text="是" inactive-text="否" />
                        </el-form-item>
                    </el-col>

                    <el-col :span="8">
                        <el-form-item label="固定标签">
                            <el-switch v-model="form.affix" active-text="是" inactive-text="否" />
                        </el-form-item>
                    </el-col>
                </el-row>
            </template>

            <!-- ================================================= -->
            <!-- 描述 -->
            <!-- ================================================= -->

            <el-divider content-position="left">
                其他信息
            </el-divider>

            <el-form-item label="菜单标题" prop="title">
                <el-input v-model="form.title" maxlength="50" placeholder="浏览器 Tab 标题" />
            </el-form-item>

            <el-form-item label="描述" prop="description">
                <el-input v-model="form.description" type="textarea" :rows="3" maxlength="255" show-word-limit
                    placeholder="请输入菜单描述" />
            </el-form-item>
        </el-form>

        <template #footer>
            <el-button @click="visible = false">
                取消
            </el-button>

            <el-button type="primary" :loading="submitting" @click="handleSubmit">
                保存
            </el-button>
        </template>
    </el-dialog>
</template>

<script setup lang="ts">
import {
    computed,
    reactive,
    ref,
} from "vue";

import type {
    FormInstance,
    FormRules,
} from "element-plus";



import IconSelect from "./IconSelect.vue";

import type {
    MenuTable,
    MenuForm as ApiMenuForm,
} from "@/api/module_system/menu";

const props = withDefaults(
    defineProps<{
        modelValue: boolean;
        data?: MenuTable | null;
        parentId?: number | null;
        menuTree?: MenuTable[];
    }>(),
    {
        data: null,
        parentId: null,
        menuTree: () => [],
    }
);

const emit = defineEmits<{
    (
        e: "update:modelValue",
        value: boolean
    ): void;

    (
        e: "success"
    ): void;

    (
        e: "submit",
        value: ApiMenuForm
    ): void;
}>();

const visible = computed({
    get: () => props.modelValue,

    set: value =>
        emit(
            "update:modelValue",
            value
        ),
});

const formRef =
    ref<FormInstance>();

const submitting =
    ref(false);

/**
 * 表单
 */
const form = reactive<any>(
    createDefaultForm()
);

/**
 * 是否编辑
 */
const isEdit = computed(
    () => !!props.data?.id
);

/**
 * Dialog 标题
 */
const dialogTitle =
    computed(() =>
        isEdit.value
            ? "编辑菜单"
            : "新增菜单"
    );

/**
 * type 1 / 2 显示路由配置
 */
const showRouteConfig =
    computed(() =>
        form.type === 1 ||
        form.type === 2
    );

/**
 * type 1 / 2 显示路由选项
 */
const showRouteOptions =
    computed(() =>
        form.type === 1 ||
        form.type === 2
    );

/**
 * 权限字段
 *
 * type=3 必填
 *
 * 其他类型也允许填写。
 */
const showPermission =
    computed(() =>
        true
    );

/**
 * 父菜单树
 *
 * 编辑时排除当前节点以及当前节点的所有子节点，
 * 防止自己选择自己或选择自己的子节点作为父级。
 */
const parentOptions =
    computed(() => {
        const currentId =
            props.data?.id;

        return filterParentTree(
            props.menuTree,
            currentId
        );
    });

/**
 * 表单校验
 */
const rules: FormRules = {
    name: [
        {
            required: true,
            message: "请输入菜单名称",
            trigger: "blur",
        },
    ],

    type: [
        {
            required: true,
            message: "请选择菜单类型",
            trigger: "change",
        },
    ],

    order: [
        {
            required: true,
            message: "请输入显示顺序",
            trigger: "change",
        },
    ],

    permission: [
        {
            validator: (
                _rule,
                value,
                callback
            ) => {
                if (
                    form.type === 3 &&
                    !String(value || "").trim()
                ) {
                    callback(
                        new Error(
                            "权限类型必须填写权限标识"
                        )
                    );

                    return;
                }

                callback();
            },

            trigger: "blur",
        },
    ],

    route_name: [
        {
            validator: (
                _rule,
                value,
                callback
            ) => {
                if (
                    (form.type === 1 ||
                        form.type === 2) &&
                    !String(value || "").trim()
                ) {
                    callback(
                        new Error(
                            "目录和菜单必须填写路由名称"
                        )
                    );

                    return;
                }

                callback();
            },

            trigger: "blur",
        },
    ],

    route_path: [
        {
            validator: (
                _rule,
                value,
                callback
            ) => {
                if (
                    form.type === 1 ||
                    form.type === 2
                ) {
                    const path =
                        String(value || "").trim();

                    if (!path) {
                        callback(
                            new Error(
                                "目录和菜单必须填写路由地址"
                            )
                        );

                        return;
                    }

                    if (!path.startsWith("/")) {
                        callback(
                            new Error(
                                "路由地址必须以 / 开头"
                            )
                        );

                        return;
                    }
                }

                callback();
            },

            trigger: "blur",
        },
    ],

    component_path: [
        {
            validator: (
                _rule,
                value,
                callback
            ) => {
                if (form.type === 2) {
                    const path =
                        String(value || "").trim();

                    if (!path) {
                        callback(
                            new Error(
                                "菜单类型必须填写组件路径"
                            )
                        );

                        return;
                    }

                    if (path.startsWith("/")) {
                        callback(
                            new Error(
                                "组件路径不能以 / 开头"
                            )
                        );

                        return;
                    }
                }

                callback();
            },

            trigger: "blur",
        },
    ],

    redirect: [
        {
            validator: (
                _rule,
                value,
                callback
            ) => {
                if (
                    form.type === 1 &&
                    !String(value || "").trim()
                ) {
                    callback(
                        new Error(
                            "目录类型必须填写重定向地址"
                        )
                    );

                    return;
                }

                callback();
            },

            trigger: "blur",
        },
    ],
};

/**
 * 创建默认表单
 */
function createDefaultForm() {
    return {
        name: "",

        type: 2,

        icon: "",

        order: 999,

        permission: "",

        route_name: "",

        route_path: "",

        component_path: "",

        redirect: "",

        parent_id: undefined,

        keep_alive: true,

        hidden: false,

        always_show: false,

        title: "",

        params: [],

        affix: false,

        client: "pc",

        status: "0",

        description: "",
    };
}

/**
 * 初始化表单
 */
function resetForm() {
    Object.assign(
        form,
        createDefaultForm()
    );

    form.parent_id =
        props.parentId ??
        undefined;

    form.client =
        props.data?.client ||
        "pc";
}

/**
 * 编辑数据转换
 */
function loadData() {
    resetForm();

    if (!props.data) {
        return;
    }

    Object.assign(
        form,
        {
            ...props.data,

            parent_id:
                props.data.parent_id ??
                undefined,

            status:
                props.data.status ??
                "0",

            client:
                props.data.client ??
                "pc",

            params:
                props.data.params
                    ? [...props.data.params]
                    : [],
        }
    );
}

/**
 * 类型切换
 *
 * 切换类型时清理不属于当前类型的数据。
 */
function handleTypeChange(
    type: number
) {
    if (type === 1) {
        form.component_path = "";
    }

    if (type === 2) {
        form.redirect = "";
    }

    if (type === 3) {
        form.route_name = "";
        form.route_path = "";
        form.component_path = "";
        form.redirect = "";

        form.keep_alive = false;
        form.hidden = true;
        form.always_show = false;
        form.affix = false;
    }

    if (type === 4) {
        form.route_name = "";
        form.component_path = "";
        form.redirect = "";
    }

    formRef.value?.clearValidate();
}

/**
 * 提交
 */
async function handleSubmit() {
    if (!formRef.value) {
        return;
    }

    const valid =
        await formRef.value.validate();

    if (!valid) {
        return;
    }

    submitting.value = true;

    try {
        const payload: ApiMenuForm & {
            status?: string;
            description?: string;
        } = {
            name:
                String(form.name || "")
                    .trim(),

            type:
                Number(form.type),

            order:
                Number(form.order),

            permission:
                cleanString(form.permission),

            icon:
                cleanString(form.icon),

            route_name:
                cleanString(form.route_name),

            route_path:
                cleanString(form.route_path),

            component_path:
                cleanString(
                    form.component_path
                ),

            redirect:
                cleanString(form.redirect),

            hidden:
                !!form.hidden,

            keep_alive:
                !!form.keep_alive,

            always_show:
                !!form.always_show,

            title:
                cleanString(form.title),

            params:
                form.params?.length
                    ? form.params
                    : undefined,

            affix:
                !!form.affix,

            parent_id:
                form.parent_id
                    ? Number(form.parent_id)
                    : undefined,

            client:
                form.client,

            status:
                form.status || "0",

            description:
                cleanString(
                    form.description
                ),
        };

        /**
         * 将不属于当前类型的字段彻底清理。
         */
        if (payload.type === 1) {
            payload.component_path =
                undefined;
        }

        if (payload.type === 2) {
            payload.redirect =
                undefined;
        }

        if (payload.type === 3) {
            payload.route_name =
                undefined;

            payload.route_path =
                undefined;

            payload.component_path =
                undefined;

            payload.redirect =
                undefined;

            payload.keep_alive =
                false;

            payload.hidden =
                true;

            payload.always_show =
                false;

            payload.affix =
                false;
        }

        if (payload.type === 4) {
            payload.route_name =
                undefined;

            payload.component_path =
                undefined;

            payload.redirect =
                undefined;
        }

        emit(
            "success"
        );

        /**
         * 这里真正的保存交给父组件。
         *
         * 父组件会调用 store create / update。
         */
        emitFormSubmit(
            payload
        );
    } finally {
        submitting.value = false;
    }
}

/**
 * 向父组件发送表单
 *
 * 为了保持组件接口简单，使用自定义事件。
 */
function emitFormSubmit(
    payload: ApiMenuForm
) {
    emit(
        "submit",
        payload
    );
}

/**
 * 清理字符串
 */
function cleanString(
    value: unknown
) {
    const text =
        String(value ?? "")
            .trim();

    return text || undefined;
}

/**
 * 过滤父菜单树
 */
function filterParentTree(
    list: MenuTable[],
    currentId?: number
): MenuTable[] {
    return list
        .filter(
            item =>
                item.id !== currentId
        )
        .map(
            item => ({
                ...item,

                children:
                    item.children
                        ? filterParentTree(
                            item.children,
                            currentId
                        )
                        : undefined,
            })
        );
}

/**
 * Dialog 关闭
 */
function handleClosed() {
    formRef.value?.resetFields();

    resetForm();
}

/**
 * 监听 Dialog 打开
 */
import {
    watch,
} from "vue";

watch(
    () => props.modelValue,
    visible => {
        if (visible) {
            loadData();
        }
    },
    {
        immediate: true,
    }
);
</script>

<style scoped lang="scss">
.form-tip {
    margin-top: 4px;

    color: var(--el-text-color-secondary);

    font-size: 12px;
    line-height: 18px;
}
</style>