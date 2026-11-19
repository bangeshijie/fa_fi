<template>
    <el-container class="layout_container">

        <!-- ==================== 左侧菜单 ==================== -->
        <el-aside class="layout_slider" :class="{ fold: layoutSettingStore.fold }">
            <Logo />

            <el-scrollbar class="scrollbar">
                <el-menu :collapse="layoutSettingStore.fold" :default-active="$route.path" class="scrollbarmenu" router>
                    <MainMenu :menuList="menuList" />
                </el-menu>
            </el-scrollbar>
        </el-aside>


        <!-- ==================== 右侧区域 ==================== -->
        <el-container class="layout_right">

            <!-- 顶部 -->
            <el-header class="layout_tabbar" :class="{ fold: layoutSettingStore.fold }">
                <Tabbar />
            </el-header>


            <!-- ==================== 主体 ==================== -->
            <el-main class="layout_main" :class="{ fold: layoutSettingStore.fold }">

                <!--
                    注意：

                    Layout 不再负责 router-view。

                    路由页面交给 RouteView.vue。
                -->
                <div class="main-content">
                    <RouteView />
                </div>


                <!-- ==================== 底部备案 ==================== -->
                <footer class="site-footer">
                    <div class="footer-content">

                        <a href="https://beian.mps.gov.cn/#/query/webSearch?code=33010902004606" rel="noreferrer"
                            target="_blank" class="footer-link">
                            <img src="@/assets/images/gongan.png" style="
                                    width: 16px;
                                    height: 16px;
                                    display: inline-block;
                                    vertical-align: middle;
                                    margin-right: 4px;
                                    border: 0;
                                " alt="" />

                            浙公网安备33010902004606号
                        </a>


                        <span class="divider">
                            |
                        </span>


                        <a href="https://beian.miit.gov.cn/" target="_blank" class="footer-link">
                            浙ICP备2026020450号-1
                        </a>

                    </div>
                </footer>

            </el-main>

        </el-container>

    </el-container>
</template>


<script setup lang="ts">

import { computed } from 'vue'

import Logo from './logo/index.vue'
import MainMenu from './menu/index.vue'
import Tabbar from './tabbar/index.vue'
import RouteView from './components/RouteView.vue'

import { useAuthStore } from '@/store/auth.ts'
import useLayoutSettingStore from '@/store/layoutsetting'
import { constantMenuRoutes } from '@/router/routes'
import type { AppRouteRecord } from '@/types/router'


const authStore = useAuthStore()

const layoutSettingStore =
    useLayoutSettingStore()

/**
 * 侧边栏由固定菜单和权限菜单共同组成。
 *
 * Home 和 About 已经是常量路由，不应该等待后端菜单权限返回；动态菜单
 * 仍然来自 authStore.routeList。固定菜单按“首页、动态菜单、关于”的顺序
 * 组合，且额外过滤固定菜单，防止后端仍保留同名菜单时出现重复菜单项。
 */
const menuList = computed<AppRouteRecord[]>(() => {
    const homeRoutes = constantMenuRoutes.filter(
        route => route.name === 'Home',
    ) as AppRouteRecord[]

    const aboutRoutes = constantMenuRoutes.filter(
        route => route.name === 'About',
    ) as AppRouteRecord[]

    const dynamicRoutes = authStore.routeList.filter(route =>
        !constantMenuRoutes.some(fixedRoute => {
            const fixedPath = String(fixedRoute.path || '')
                .replace(/^\/+/, '')
            const dynamicPath = String(route.path || '')
                .replace(/^\/+/, '')

            return (
                fixedRoute.name === route.name ||
                fixedPath === dynamicPath
            )
        }),
    )

    return [
        ...homeRoutes,
        ...dynamicRoutes,
        ...aboutRoutes,
    ]
})

</script>


<style lang="scss">
.layout_container {
    width: 100%;
    height: 100vh;


    /* ==================== 左侧菜单 ==================== */

    .layout_slider {
        width: $base-menu-width;
        height: 100vh;

        background-color: var(--app-menu-bg);
        border-right: 1px solid var(--app-border);

        transition: all 0.3s;

        overflow: hidden;


        .scrollbar {
            width: 100%;

            height:
                calc(100vh - $base-menu-logo-height );

            overflow: hidden;


            :deep(.el-scrollbar__wrap) {
                overflow-x: hidden !important;
                overflow-y: auto;
            }


            .scrollbarmenu {
                --el-menu-bg-color: var(--app-menu-bg);

                --el-menu-text-color: var(--app-muted);

                --el-menu-active-color: var(--el-color-primary) !important;

                --el-menu-hover-bg-color: var(--app-menu-hover);

                --el-menu-hover-text-color: var(--app-menu-active-text);

                border-right: 0;

                :deep(.el-menu-item),
                :deep(.el-sub-menu__title) {
                    border-radius: 0;
                    transition: background-color .18s ease, color .18s ease;
                }

                :deep(.el-menu-item:hover),
                :deep(.el-sub-menu__title:hover) {
                    background-color: var(--app-menu-hover);
                    color: var(--el-color-primary);
                }

                :deep(.el-menu-item:hover .menu-label),
                :deep(.el-sub-menu__title:hover .menu-label) {
                    display: inline-block;
                    color: var(--el-color-primary);
                    transform: scale(1.1);
                    transform-origin: left center;
                }

                :deep(.el-menu-item.is-active) {
                    background-color: var(--app-menu-active);
                    color: var(--el-color-primary);
                    font-weight: 600;
                }

                :deep(.el-sub-menu.is-active > .el-sub-menu__title) {
                    color: var(--el-color-primary);
                }


                &.el-menu--collapse {

                    width:
                        $base-menu-min-width !important;


                    .el-menu-item,
                    .el-sub-menu__title {

                        overflow: hidden;

                        text-overflow: ellipsis;

                        white-space: nowrap;
                    }
                }



            }
        }


        /* 折叠 */

        &.fold {

            width:
                $base-menu-min-width;


            .scrollbar {

                :deep(.el-scrollbar__wrap) {

                    overflow:
                        hidden !important;
                }
            }
        }
    }


    /* ==================== 右侧 ==================== */

    .layout_right {

        display: flex;

        flex-direction: column;

        height: 100vh;

        flex: 1;
    }


    /* ==================== 顶部 ==================== */

    .layout_tabbar {

        height:
            $base-tabbar-height !important;

        flex-shrink: 0;

        background-color: var(--app-page-bg);

        z-index: 999;

        transition: all 0.3s;

        padding:
            0 !important;
    }


    /* ==================== 主体 ==================== */

    .layout_main {

        flex: 1;

        background-color: var(--app-page-bg);

        padding:
            20px;

        overflow: auto;

        transition: all 0.3s;

        display: flex;

        flex-direction: column;


        .main-content {

            /*
             * 不再用 flex: 1 把 footer 推到可视区域底部。
             * 保留首屏高度，让 footer 位于内容流末尾，需要滚动到底部才显示。
             */
            flex: 0 0 auto;

            min-height:
                calc(100vh - $base-tabbar-height - 40px);
        }


        /* ==================== 底部 ==================== */

        .site-footer {

            width: 100%;

            padding:
                15px 0;

            margin-top:
                24px;

            border-top: 1px solid var(--app-border);

            flex-shrink: 0;


            .footer-content {

                display: flex;

                justify-content:
                    center;

                align-items:
                    center;

                font-size:
                    12px;

                color: var(--app-muted);


                .divider {

                    margin:
                        0 10px;

                    color: var(--app-border);
                }


                .footer-link {

                    color: var(--app-muted);

                    text-decoration:
                        none;

                    transition:
                        color 0.3s;


                    &:hover {

                        color: var(--el-color-primary);
                    }
                }
            }
        }
    }
}
</style>
