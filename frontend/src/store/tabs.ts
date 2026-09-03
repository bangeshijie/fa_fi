// store/tabs.ts

import { defineStore } from "pinia";
import type { RouteLocationNormalized } from "vue-router";
import { ref, computed } from "vue";


/**
 * =========================================================
 * Tab 类型
 * =========================================================
 */
export interface TabItem {

    /** 路由路径 */
    path: string;

    /** 路由名称 */
    name?: string;

    /** 标签标题 */
    title?: string;

    /** 菜单图标 */
    icon?: string;

    /** 是否隐藏 */
    hidden?: boolean;

    /** 是否缓存 */
    keepAlive?: boolean;

    /** 是否固定 */
    affix?: boolean;

    /** 路由 query */
    query?: Record<string, any>;

    /** 路由 params */
    params?: Record<string, any>;
}


/**
 * =========================================================
 * Store
 * =========================================================
 */
export const useTabsStore = defineStore(
    "userTabs",
    () => {

        /**
         * =====================================================
         * 状态
         * =====================================================
         */

        /** 当前打开的标签页 */
        const tabs =
            ref<TabItem[]>([]);

        /** 当前激活的标签页 */
        const activeTab =
            ref<string>("");

        /**
         * 页面刷新状态
         *
         * path -> number
         *
         * 每刷新一次 +1
         */
        const refreshMap =
            ref<Record<string, number>>({});


        /**
         * =====================================================
         * 计算属性
         * =====================================================
         */

        /**
         * KeepAlive 缓存页面名称
         *
         * 注意：
         *
         * Vue KeepAlive 的 include
         * 匹配的是组件 name。
         *
         * 因此这里返回：
         *
         * [
         *     "User",
         *     "Menu",
         *     "Role"
         * ]
         */
        const cachedViews = computed(() => {

            return tabs.value
                .filter(tab =>
                    tab.name &&
                    tab.keepAlive === true &&
                    tab.path !== "/home"
                )
                .map(tab => tab.name!)
                .filter(Boolean);

        });


        /**
         * 固定标签页
         */
        const affixTabs = computed(() => {

            return tabs.value.filter(
                tab => tab.affix === true
            );

        });


        /**
         * =====================================================
         * Affix
         * =====================================================
         */

        /**
         * 切换固定状态
         */
        const toggleAffix = (
            path: string
        ) => {

            const tab =
                tabs.value.find(
                    item => item.path === path
                );

            if (tab) {
                tab.affix = !tab.affix;
            }

        };


        /**
         * 设置固定状态
         */
        const setAffix = (
            path: string,
            affix: boolean
        ) => {

            const tab =
                tabs.value.find(
                    item => item.path === path
                );

            if (tab) {
                tab.affix = affix;
            }

        };


        /**
         * =====================================================
         * 刷新
         * =====================================================
         */

        /**
         * 刷新指定 Tab
         */
        const refreshTab = (
            path: string
        ) => {

            refreshMap.value[path] =
                (refreshMap.value[path] || 0) + 1;

        };


        /**
         * 刷新当前 Tab
         */
        const refreshCurrentTab = () => {

            if (activeTab.value) {

                refreshTab(
                    activeTab.value
                );

            }

        };


        /**
         * 刷新所有 Tab
         */
        const refreshAllTabs = () => {

            tabs.value.forEach(tab => {

                refreshTab(
                    tab.path
                );

            });

        };


        /**
         * 获取刷新 key
         */
        const getRefreshKey = (
            path: string
        ) => {

            return (
                refreshMap.value[path] || 0
            );

        };


        /**
         * =====================================================
         * 添加 Tab
         * =====================================================
         */

        const addTab = (
            route: RouteLocationNormalized
        ) => {

            /**
             * 隐藏路由不进入 Tab
             */
            if (
                route.meta?.hidden ||
                route.path === "/login" ||
                route.path === "/404"
            ) {

                return;

            }


            /**
             * 无路径不处理
             */
            if (!route.path) {
                return;
            }


            /**
             * 当前路由是否已经存在
             */
            const existIndex =
                tabs.value.findIndex(
                    item =>
                        item.path === route.path
                );


            /**
             * =================================================
             * 已存在
             * =================================================
             */
            if (existIndex !== -1) {

                const existingTab =
                    tabs.value[existIndex];

                if (!existingTab) {
                    return;
                }


                tabs.value[existIndex] = {

                    ...existingTab,

                    title:
                        route.meta?.title ||
                        existingTab.title,

                    icon:
                        route.meta?.icon ||
                        existingTab.icon,

                    query:
                        route.query as Record<
                            string,
                            any
                        >,

                    params:
                        route.params as Record<
                            string,
                            any
                        >,

                    /**
                     * 路由本身的配置
                     * 不因为重复进入而改变 affix
                     */
                    affix:
                        existingTab.affix,

                    /**
                     * 保持最新缓存配置
                     */
                    keepAlive:
                        route.meta?.keepAlive === true,

                    hidden:
                        route.meta?.hidden === true,

                };


                activeTab.value =
                    route.path;

                return;
            }


            /**
             * =================================================
             * 新建 Tab
             * =================================================
             */

            const tab: TabItem = {

                path:
                    route.path,

                name:
                    typeof route.name === "string"
                        ? route.name
                        : undefined,

                title:
                    route.meta?.title ||
                    "未命名",

                icon:
                    route.meta?.icon ||
                    undefined,

                hidden:
                    route.meta?.hidden === true,

                keepAlive:
                    route.meta?.keepAlive === true,

                affix:
                    route.meta?.affix === true,

                query:
                    route.query as Record<
                        string,
                        any
                    >,

                params:
                    route.params as Record<
                        string,
                        any
                    >,

            };


            tabs.value.push(tab);

            activeTab.value =
                tab.path;

        };


        /**
         * =====================================================
         * 删除 Tab
         * =====================================================
         */

        const removeTab = (
            path: string
        ) => {

            const index =
                tabs.value.findIndex(
                    item =>
                        item.path === path
                );

            if (index === -1) {
                return;
            }


            const tab =
                tabs.value[index];

            if (!tab) {
                return;
            }


            /**
             * 固定 Tab 不允许关闭
             */
            if (tab.affix) {
                return;
            }


            tabs.value.splice(
                index,
                1
            );


            delete refreshMap.value[path];


            /**
             * 如果删除的是当前 Tab
             */
            if (
                activeTab.value === path
            ) {

                if (
                    tabs.value.length > 0
                ) {

                    const newIndex =
                        Math.min(
                            index,
                            tabs.value.length - 1
                        );

                    const nextTab =
                        tabs.value[newIndex];

                    if (nextTab) {

                        activeTab.value =
                            nextTab.path;

                    }

                } else {

                    activeTab.value =
                        "";

                }

            }

        };


        /**
         * =====================================================
         * 当前 Tab
         * =====================================================
         */

        const setActiveTab = (
            path: string
        ) => {

            activeTab.value =
                path;

        };


        /**
         * =====================================================
         * 关闭其他
         * =====================================================
         */

        const closeOtherTabs = (
            path: string
        ) => {

            const keepPaths =
                new Set([
                    path,
                    ...affixTabs.value.map(
                        tab => tab.path
                    ),
                ]);


            Object.keys(
                refreshMap.value
            ).forEach(key => {

                if (!keepPaths.has(key)) {

                    delete refreshMap.value[key];

                }

            });


            tabs.value =
                tabs.value.filter(
                    item =>
                        keepPaths.has(
                            item.path
                        )
                );


            activeTab.value =
                path;

        };


        /**
         * =====================================================
         * 关闭所有
         * =====================================================
         */

        const closeAllTabs = (): string | null => {

            const affixPaths =
                affixTabs.value.map(
                    tab => tab.path
                );


            tabs.value =
                tabs.value.filter(
                    item =>
                        affixPaths.includes(
                            item.path
                        )
                );


            Object.keys(
                refreshMap.value
            ).forEach(key => {

                if (
                    !affixPaths.includes(key)
                ) {

                    delete refreshMap.value[key];

                }

            });


            /**
             * 如果有固定 Tab
             */
            if (
                affixPaths.length > 0
            ) {

                const firstAffixPath =
                    affixPaths[0];

                if (firstAffixPath) {

                    activeTab.value =
                        firstAffixPath;

                    return firstAffixPath;

                }

            }


            activeTab.value =
                "";

            return null;

        };


        /**
         * =====================================================
         * 关闭左侧
         * =====================================================
         */

        const closeLeft = (
            path: string
        ) => {

            const currentIndex =
                tabs.value.findIndex(
                    tab =>
                        tab.path === path
                );


            if (currentIndex <= 0) {
                return;
            }


            const affixPaths =
                affixTabs.value.map(
                    tab => tab.path
                );


            const keepPaths =
                new Set([
                    ...affixPaths,
                    path,
                    ...tabs.value
                        .slice(currentIndex)
                        .map(tab => tab.path),
                ]);


            Object.keys(
                refreshMap.value
            ).forEach(key => {

                if (
                    !keepPaths.has(key)
                ) {

                    delete refreshMap.value[key];

                }

            });


            tabs.value =
                tabs.value.filter(
                    item =>
                        keepPaths.has(
                            item.path
                        )
                );


            /**
             * 固定 Tab 始终放前面
             */
            const fixed =
                tabs.value.filter(
                    tab => tab.affix
                );

            const normal =
                tabs.value.filter(
                    tab => !tab.affix
                );


            tabs.value = [
                ...fixed,
                ...normal,
            ];


            activeTab.value =
                path;

        };


        /**
         * =====================================================
         * 关闭右侧
         * =====================================================
         */

        const closeRight = (
            path: string
        ) => {

            const currentIndex =
                tabs.value.findIndex(
                    tab =>
                        tab.path === path
                );


            if (
                currentIndex === -1 ||
                currentIndex >=
                    tabs.value.length - 1
            ) {

                return;

            }


            const affixPaths =
                affixTabs.value.map(
                    tab => tab.path
                );


            const keepPaths =
                new Set([
                    ...affixPaths,
                    path,
                    ...tabs.value
                        .slice(
                            0,
                            currentIndex + 1
                        )
                        .map(
                            tab => tab.path
                        ),
                ]);


            Object.keys(
                refreshMap.value
            ).forEach(key => {

                if (
                    !keepPaths.has(key)
                ) {

                    delete refreshMap.value[key];

                }

            });


            tabs.value =
                tabs.value.filter(
                    item =>
                        keepPaths.has(
                            item.path
                        )
                );


            /**
             * 固定 Tab 放前面
             */
            const fixed =
                tabs.value.filter(
                    tab => tab.affix
                );

            const normal =
                tabs.value.filter(
                    tab => !tab.affix
                );


            tabs.value = [
                ...fixed,
                ...normal,
            ];


            activeTab.value =
                path;

        };


        /**
         * =====================================================
         * 返回 Store
         * =====================================================
         */

        return {

            tabs,

            activeTab,

            refreshMap,

            cachedViews,

            affixTabs,

            refreshTab,

            refreshCurrentTab,

            refreshAllTabs,

            getRefreshKey,

            toggleAffix,

            setAffix,

            addTab,

            removeTab,

            setActiveTab,

            closeOtherTabs,

            closeAllTabs,

            closeLeft,

            closeRight,

        };

    },
    {

        persist: {

            key: "tabs",

            storage: sessionStorage,

            pick: [
                "tabs",
                "activeTab",
            ],

        },

    }
);