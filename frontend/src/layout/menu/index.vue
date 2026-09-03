<template>
    <template v-for="item in menuList" :key="item.name || item.path">

        <!-- ============================= -->
        <!-- 没有子菜单：真正页面 -->
        <!-- ============================= -->
        <el-menu-item v-if="!item.children || item.children.length === 0" :index="getMenuPath(item)">

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
