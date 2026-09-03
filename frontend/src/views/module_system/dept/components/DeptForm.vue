<template>
    <el-dialog v-model="visible" :title="isEdit ? '编辑部门' : '新增部门'" width="600px" destroy-on-close
        @closed="handleClosed">
        <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
            <!-- 部门名称 -->
            <el-form-item label="部门名称" prop="name">
                <el-input v-model="form.name" maxlength="64" show-word-limit placeholder="请输入部门名称" clearable />
            </el-form-item>

            <!-- 部门编码 -->
            <el-form-item label="部门编码" prop="code">
                <el-input v-model="form.code" maxlength="16" show-word-limit placeholder="请输入部门编码" clearable />
            </el-form-item>

            <!-- 上级部门 -->
            <el-form-item label="上级部门" prop="parent_id">
                <el-tree-select v-model="form.parent_id" :data="parentTree" node-key="id" check-strictly clearable
                    filterable default-expand-all placeholder="请选择上级部门" style="width: 100%" :props="{
                        label: 'name',
                        children: 'children',
                    }" />
            </el-form-item>

            <!-- 排序 -->
            <el-form-item label="显示排序" prop="order">
                <el-input-number v-model="form.order" :min="0" :max="9999" controls-position="right"
                    style="width: 100%" />
            </el-form-item>

            <!-- 负责人 -->
            <el-form-item label="负责人" prop="leader">
                <el-input v-model="form.leader" maxlength="32" placeholder="请输入部门负责人" clearable />
            </el-form-item>

            <!-- 手机 -->
            <el-form-item label="联系电话" prop="phone">
                <el-input v-model="form.phone" maxlength="11" placeholder="请输入联系电话" clearable />
            </el-form-item>

            <!-- 邮箱 -->
            <el-form-item label="邮箱" prop="email">
                <el-input v-model="form.email" maxlength="64" placeholder="请输入邮箱" clearable />
            </el-form-item>

            <!-- 状态 -->
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

            <!-- 描述 -->
            <el-form-item label="备注说明" prop="description">
                <el-input v-model="form.description" type="textarea" :rows="3" maxlength="255" show-word-limit
                    placeholder="请输入备注说明" />
            </el-form-item>
        </el-form>

        <template #footer>
            <div class="dialog-footer">
                <el-button @click="visible = false">
                    取消
                </el-button>

                <el-button type="primary" :loading="loading" @click="handleSubmit">
                    确定
                </el-button>
            </div>
        </template>
    </el-dialog>
</template>

<script setup lang="ts">
import {
    computed,
    nextTick,
    ref,
    watch,
} from "vue";

import type {
    FormInstance,
    FormRules,
} from "element-plus";

import type {
    DeptForm,
    DeptTable,
} from "@/api/module_system/dept";

interface Props {
    modelValue: boolean;

    data?: DeptTable | null;

    parentId?: number | null;

    deptTree: DeptTable[];
}

const props =
    withDefaults(
        defineProps<Props>(),
        {
            data: null,
            parentId: null,
        }
    );

const emit =
    defineEmits<{
        (
            e: "update:modelValue",
            value: boolean
        ): void;

        (
            e: "submit",
            form: DeptForm
        ): void;
    }>();

// =========================================================
// Dialog
// =========================================================

const visible = computed({
    get: () =>
        props.modelValue,

    set: value =>
        emit(
            "update:modelValue",
            value
        ),
});

// =========================================================
// 表单
// =========================================================

const formRef =
    ref<FormInstance>();

const loading =
    ref(false);

const isEdit =
    computed(
        () => !!props.data?.id
    );

const form =
    ref<DeptForm>(
        createDefaultForm()
    );

// =========================================================
// 上级部门树
// =========================================================

const parentTree =
    computed(() => {
        return filterParentTree(
            props.deptTree
        );
    });

// =========================================================
// 校验
// =========================================================

const rules: FormRules = {
    name: [
        {
            required: true,
            message:
                "请输入部门名称",
            trigger: "blur",
        },
    ],

    code: [
        {
            required: true,
            message:
                "请输入部门编码",
            trigger: "blur",
        },
    ],

    order: [
        {
            required: true,
            message:
                "请输入显示排序",
            trigger: "blur",
        },
    ],
};

// =========================================================
// 初始化
// =========================================================

watch(
    () => props.modelValue,
    async value => {
        if (!value) {
            return;
        }

        await nextTick();

        resetForm();

        if (props.data) {
            form.value = {
                name:
                    props.data.name || "",

                code:
                    props.data.code || "",

                order:
                    props.data.order ?? 1,

                leader:
                    props.data.leader || "",

                phone:
                    props.data.phone || "",

                email:
                    props.data.email || "",

                parent_id:
                    props.data.parent_id ??
                    undefined,

                status:
                    props.data.status || "0",

                description:
                    props.data.description ||
                    "",
            };
        } else {
            form.value.parent_id =
                props.parentId ??
                undefined;
        }
    }
);

// =========================================================
// 默认表单
// =========================================================

function createDefaultForm(): DeptForm {
    return {
        name: "",

        code: "",

        order: 1,

        leader: "",

        phone: "",

        email: "",

        parent_id:
            undefined,

        status: "0",

        description: "",
    };
}

// =========================================================
// 重置
// =========================================================

function resetForm() {
    form.value =
        createDefaultForm();

    formRef.value?.clearValidate();
}

// =========================================================
// 过滤上级部门
// =========================================================

function filterParentTree(
    tree: DeptTable[]
): DeptTable[] {
    if (!props.data?.id) {
        return tree;
    }

    const currentId =
        props.data.id;

    const forbiddenIds =
        new Set<number>();

    /**
     * 收集当前部门以及所有子部门
     */
    function collectIds(
        node: DeptTable
    ) {
        if (node.id !== undefined) {
            forbiddenIds.add(
                node.id
            );
        }

        node.children?.forEach(
            child => {
                collectIds(child);
            }
        );
    }

    /**
     * 找到当前编辑部门
     */
    function findNode(
        nodes: DeptTable[]
    ): DeptTable | undefined {
        for (const node of nodes) {
            if (
                node.id === currentId
            ) {
                return node;
            }

            if (node.children?.length) {
                const result =
                    findNode(
                        node.children
                    );

                if (result) {
                    return result;
                }
            }
        }

        return undefined;
    }

    const currentNode =
        findNode(tree);

    if (currentNode) {
        collectIds(currentNode);
    }

    /**
     * 删除当前部门及其所有子部门
     */
    function filterTree(
        nodes: DeptTable[]
    ): DeptTable[] {
        return nodes
            .filter(
                node =>
                    node.id === undefined ||
                    !forbiddenIds.has(
                        node.id
                    )
            )
            .map(node => ({
                ...node,

                children:
                    node.children?.length
                        ? filterTree(
                            node.children
                        )
                        : undefined,
            }));
    }

    return filterTree(tree);
}

// =========================================================
// 提交
// =========================================================

async function handleSubmit() {
    if (!formRef.value) {
        return;
    }

    try {
        await formRef.value.validate();

        loading.value = true;

        emit(
            "submit",
            {
                ...form.value,
            }
        );
    } finally {
        loading.value = false;
    }
}

// =========================================================
// 关闭
// =========================================================

function handleClosed() {
    resetForm();
}
</script>