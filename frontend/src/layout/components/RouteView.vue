<script setup lang="ts">
import {
    computed,
    ref,
    nextTick,
    watch,
} from 'vue'

import {
    RouterView,
    type RouteLocationNormalizedLoaded,
} from 'vue-router'

import { useTabsStore } from '@/store/tabs'
import useLayoutSettingStore from '@/store/layoutsetting'

defineOptions({
    name: 'RouteView',
})

const tabsStore = useTabsStore()

const layoutSettingStore =
    useLayoutSettingStore()

/**
 * KeepAlive 缓存页面
 */
const cachedViews = computed(() => {
    return tabsStore.cachedViews
})

/**
 * 页面刷新
 */
const isRefresh = ref(true)

const refreshView = async () => {

    isRefresh.value = false

    await nextTick()

    isRefresh.value = true
}

/**
 * 监听 Layout 刷新按钮
 */
watch(
    () => layoutSettingStore.refresh,
    () => {
        refreshView()
    },
    {
        flush: 'post',
    },
)

/**
 * 页面 Key
 */
function getRouteKey(
    route: RouteLocationNormalizedLoaded,
): string {

    // refreshMap is incremented by TabView. Including it in the key makes
    // both cached and uncached pages remount instead of only changing store state.
    const refreshKey = tabsStore.getRefreshKey(route.path)

    /**
     * 明确要求 query 变化时重新挂载
     */
    if (
        route.meta.remountOnFullPath === true
    ) {
        return `${route.fullPath}:refresh-${refreshKey}`
    }

    /**
     * 有 name：
     *
     *     name + params
     */
    if (route.name != null) {

        return `${String(route.name)}:${JSON.stringify(
            route.params ?? {},
        )}:refresh-${refreshKey}`
    }

    /**
     * 没有 name
     */
    return `${route.path}:refresh-${refreshKey}`
}
</script>

<template>

    <RouterView v-if="isRefresh" v-slot="{ Component, route }">

        <!--
            真正业务页面
        -->
        <KeepAlive v-if="route.meta.keepAlive === true" :include="cachedViews" :max="10">
            <component :is="Component" :key="getRouteKey(route)" class="route-page" />
        </KeepAlive>

        <!--
            不缓存：
            包括目录 RouteView
            和不需要缓存的业务页面
        -->
        <component v-else :is="Component" :key="getRouteKey(route)" class="route-page" />

    </RouterView>

</template>

<style scoped lang="scss">
.route-page {
    width: 100%;
    min-width: 0;
    min-height: 0;
}
</style>
