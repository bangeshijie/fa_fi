<template>
    <div class="role-permission">
        <!-- 数据权限 -->
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
                    自定义
                </el-radio>
            </el-radio-group>
        </el-card>

        <!-- 菜单权限 -->
        <el-card shadow="never" class="permission-card">
            <template #header>
                菜单权限
            </template>

            <el-tree ref="menuTreeRef" :data="menuTree" node-key="id" show-checkbox default-expand-all
                :props="treeProps" @check="handleMenuCheck" />
        </el-card>

        <!-- 部门权限 -->
        <el-card v-if="
            roleStore.permissionDataScope === 5
        " shadow="never" class="permission-card">
            <template #header>
                自定义部门权限
            </template>

            <el-tree ref="deptTreeRef" :data="deptTree" node-key="id" show-checkbox default-expand-all
                :props="treeProps" @check="handleDeptCheck" />
        </el-card>
    </div>
</template>

<script setup lang="ts">
import {
    nextTick,
    ref,
} from "vue";

import type {
    ElTree,
} from "element-plus";

import {
    ElMessage,
} from "element-plus";

import { useRoleStore } from "@/store/role";
import { useMenuStore } from "@/store/menu";
import { useDeptStore } from "@/store/dept";

const roleStore =
    useRoleStore();

const menuStore =
    useMenuStore();

const deptStore =
    useDeptStore();

const menuTreeRef =
    ref<InstanceType<typeof ElTree>>();

const deptTreeRef =
    ref<InstanceType<typeof ElTree>>();

const menuTree =
    ref(menuStore.menuTree);

const deptTree =
    ref(deptStore.deptTree);

const treeProps = {
    label: "name",
    children: "children",
};

/**
 * 加载菜单
 */
async function loadMenus() {
    try {
        await menuStore.fetchMenuTree();

        menuTree.value =
            menuStore.menuTree;
    } catch (error) {
        console.error(
            "获取菜单树失败:",
            error
        );

        ElMessage.error(
            "获取菜单权限失败"
        );
    }
}

/**
 * 加载部门
 */
async function loadDepts() {
    try {
        await deptStore.fetchDeptTree();

        deptTree.value =
            deptStore.deptTree;
    } catch (error) {
        console.error(
            "获取部门树失败:",
            error
        );

        ElMessage.error(
            "获取部门权限失败"
        );
    }
}

/**
 * 设置菜单选中状态
 */
function setMenuCheckedKeys() {
    nextTick(() => {
        menuTreeRef.value?.setCheckedKeys(
            roleStore.permissionMenuIds
        );
    });
}

/**
 * 设置部门选中状态
 */
function setDeptCheckedKeys() {
    if (
        roleStore.permissionDataScope !==
        5
    ) {
        return;
    }

    nextTick(() => {
        deptTreeRef.value?.setCheckedKeys(
            roleStore.permissionDeptIds
        );
    });
}

/**
 * 菜单选择
 */
function handleMenuCheck() {
    const keys =
        menuTreeRef.value?.getCheckedKeys(
            false
        ) as number[] | undefined;

    roleStore.setPermissionMenuIds(
        keys ?? []
    );
}

/**
 * 部门选择
 */
function handleDeptCheck() {
    const keys =
        deptTreeRef.value?.getCheckedKeys(
            false
        ) as number[] | undefined;

    roleStore.setPermissionDeptIds(
        keys ?? []
    );
}

/**
 * 初始化权限树
 */
async function init() {
    await loadMenus();

    await loadDepts();

    await nextTick();

    setMenuCheckedKeys();

    setDeptCheckedKeys();
}

defineExpose({
    init,
    setMenuCheckedKeys,
    setDeptCheckedKeys,
});
</script>

<style scoped>
.role-permission {
    max-height: 600px;
    overflow-y: auto;
}

.permission-card {
    margin-bottom: 16px;
}

.permission-card:last-child {
    margin-bottom: 0;
}
</style>