<template>
    <template v-for="item in menuList" :key="item.name || item.path">

        <!--
            目录只有一个子菜单且未开启“始终显示”时，
            直接把唯一子菜单提升到当前层级显示。
            parent-path 仍然传入父目录地址，保证点击后使用完整路由。
        -->
        <MainMenu
            v-if="shouldFlatten(item)"
            :menu-list="item.children || []"
            :parent-path="getMenuPath(item)"
        />

        <!-- ============================= -->
        <!-- 没有子菜单：真正页面 -->
        <!-- ============================= -->
        <el-menu-item v-else-if="!item.children || item.children.length === 0" :index="getMenuPath(item)">

            <el-icon v-if="item.meta?.icon">
                <component :is="item.meta.icon" />
            </el-icon>

            <template #title>
                <span class="menu-label">{{ item.meta?.title }}</span>
            </template>

        </el-menu-item>


        <!-- ============================= -->
        <!-- 有子菜单：目录 -->
        <!-- ============================= -->
        <el-sub-menu v-else :index="getMenuPath(item)">

            <template #title>

                <el-icon v-if="item.meta?.icon">
                    <component :is="item.meta.icon" />
                </el-icon>

                <span class="menu-label">{{ item.meta?.title }}</span>

            </template>


            <MainMenu :menu-list="item.children" :parent-path="getMenuPath(item)" />

        </el-sub-menu>

    </template>
</template>


<script setup lang="ts">

import type { AppRouteRecord } from '@/types/router'


defineOptions({
    name: 'MainMenu'
})


const props = withDefaults(
    defineProps<{
        menuList: AppRouteRecord[]
        parentPath?: string
    }>(),
    {
        parentPath: ''
    }
)

/**
 * 是否折叠掉只有一个子菜单的目录。
 *
 * 始终显示 = true 时保留父级目录；
 * 始终显示 = false 时直接展示唯一子菜单。
 *
 * 只有目录类型参与该规则，普通页面即使后端错误地带了 children，
 * 也不会被菜单组件改变层级语义。
 */
const shouldFlatten = (
    item: AppRouteRecord,
): boolean => {
    return (
        item.meta?.type === 1 &&
        item.meta?.alwaysShow !== true &&
        Array.isArray(item.children) &&
        item.children.length === 1
    )
}


/**
 * =========================================================
 * 获取菜单实际 URL
 * =========================================================
 *
 * 数据库：
 *
 * Platform
 * route_path = /platform
 *
 * Menu
 * route_path = menu
 *
 * 最终：
 *
 * /platform/menu
 */
const getMenuPath = (
    item: AppRouteRecord
): string => {

    const path = item.path || ''


    /**
     * 本身就是绝对路径
     *
     * /platform
     */
    if (path.startsWith('/')) {
        return path
    }


    /**
     * 子菜单
     *
     * parentPath = /platform
     * path       = menu
     *
     * => /platform/menu
     */
    if (props.parentPath) {

        return `${props.parentPath}/${path}`
            .replace(/\/+/g, '/')
    }


    /**
     * 顶级相对路径
     */
    return `/${path}`
        .replace(/\/+/g, '/')
}

</script>
