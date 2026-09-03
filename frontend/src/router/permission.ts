/**
 * =========================================================
 * 动态路由 / 权限控制
 * =========================================================
 *
 * 主要职责：
 *
 * 1. 根据后端菜单生成 Vue Router 路由
 * 2. 注册动态路由
 * 3. 收集按钮权限
 * 4. 登录后初始化动态路由
 * 5. 刷新页面后重新初始化动态路由
 * 6. 登出时清理动态路由
 * 7. 路由权限守卫
 * 8. NProgress
 */

import type {
    RouteRecordRaw,
    RouteLocationNormalized,
} from "vue-router";


import NProgress from "nprogress";
import "nprogress/nprogress.css";

import { router } from "@/router";
import setting from "../setting";

import pinia from "../store";

import { useAuthStore } from "../store/auth";
import { useTabsStore } from "../store/tabs";

import type { AppRouteRecord ,MenuType} from "@/types/router";
import RouteView from "@/layout/components/RouteView.vue";

import { Auth } from "@/utils";

/**
 * =========================================================
 * 动态路由状态
 * =========================================================
 */

/**
 * 动态路由是否已经注册
 */
let hasAddRoute = false;

/**
 * 已经注册的动态路由名称
 *
 * 登出时需要通过这些 name 删除动态路由。
 */
const dynamicRouteNames: string[] = [];


/**
 * =========================================================
 * Vite 自动扫描页面组件
 * =========================================================
 *
 * 后端 component_path 例如：
 *
 * module_system/user/index
 *
 * 对应：
 *
 * src/views/module_system/user/index.vue
 */
const modules = import.meta.glob(
    "/src/views/**/*.vue"
);


/**
 * =========================================================
 * 加载页面组件
 * =========================================================
 *
 * componentPath 有值：
 *
 *     module_system/user/index
 *
 * → 加载：
 *
 *     /src/views/module_system/user/index.vue
 *
 *
 * componentPath 没有值：
 *
 *     说明通常是目录节点。
 *
 *     目录本身不需要页面组件，
 *     使用 RouterView 承载 children。
 */
function loadComponent(
    componentPath?: string | null,
): AppRouteRecord["component"] {

    /**
     * 没有 component_path
     *
     * 一般就是目录节点。
     *
     * 目录不再使用 vue-router 自带 RouterView，
     * 而是使用我们自己的 RouteView。
     */
    if (!componentPath) {
        return RouteView;
    }

    const key =
        `/src/views/${componentPath}.vue`;

    const component =
        modules[key];

    if (!component) {

        console.error(
            "[Router] 找不到页面组件:",
            key,
        );

        return () =>
            import("@/views/404/index.vue");
    }

    return component;
}


/**
 * =========================================================
 * 规范化子路由 path
 * =========================================================
 *
 * 后端可能返回：
 *
 * 父：
 *
 *     /system
 *
 * 子：
 *
 *     /system/user
 *
 *
 * Vue Router 嵌套路由应该变成：
 *
 * 父：
 *
 *     /system
 *
 * 子：
 *
 *     user
 */
function normalizeChildPath(
    path: string,
): string {

    if (!path) {
        return "";
    }


    return path
        .replace(/^\/+/, "");
}


/**
 * =========================================================
 * 获取当前菜单完整路径
 * =========================================================
 *
 * 这里主要解决：
 *
 * 父：
 *
 *     /system
 *
 * 子：
 *
 *     /system/user
 *
 * 转换成：
 *
 *     /system
 *         └── user
 */
function resolveRoutePath(
    routePath: string | undefined | null,
    parentPath: string,
): string {

    const path =
        routePath?.trim() || "";


    /**
     * 第一层路由
     */
    if (!parentPath) {

        if (!path) {
            return "";
        }


        return path.startsWith("/")
            ? path
            : `/${path}`;
    }


    /**
     * 子路由
     */
    if (!path) {
        return "";
    }


    const normalizedParent =
        parentPath.endsWith("/")
            ? parentPath.slice(0, -1)
            : parentPath;


    const normalizedPath =
        path.startsWith("/")
            ? path
            : `/${path}`;


    const prefix =
        `${normalizedParent}/`;


    /**
     * 后端返回完整路径：
     *
     * /system/user
     *
     * → user
     */
    if (
        normalizedPath.startsWith(prefix)
    ) {

        return normalizedPath.slice(
            prefix.length,
        );
    }


    /**
     * 后端直接返回：
     *
     * user
     */
    return normalizeChildPath(
        normalizedPath,
    );
}


/**
 * =========================================================
 * 后端菜单
 * → Vue Router 路由
 * =========================================================
 *
 * 后端菜单类型：
 *
 * 1 = 目录
 * 2 = 菜单
 * 3 = 权限
 * 4 = 外链
 *
 *
 * 其中：
 *
 * type = 1
 *     目录
 *
 * type = 2
 *     页面
 *
 * type = 3
 *     按钮权限
 *
 * type = 4
 *     外链
 *
 *
 * 特别注意：
 *
 * type = 3
 *
 * 不生成 Vue Router 路由。
 *
 * 例如：
 *
 * module_system:menu:create
 * module_system:menu:update
 * module_system:menu:delete
 *
 * 这些只进入 permissions。
 */
export function generateRoutes(
    menus: any[],
    parentPath = "",
): AppRouteRecord[] {

    const routes: AppRouteRecord[] = [];


    /**
     * 防止 menus 不是数组
     */
    if (!Array.isArray(menus)) {
        return routes;
    }


    for (const item of menus) {

        if (!item) {
            continue;
        }


        const type =
            Number(item.type)as MenuType;


        /**
         * =====================================================
         * type = 3
         *
         * 按钮 / 权限
         * =====================================================
         *
         * 不生成路由。
         *
         * 权限统一由：
         *
         * collectPermissions()
         *
         * 收集。
         */
        if (type === 3) {
            continue;
        }


        /**
         * =====================================================
         * 当前路由 path
         * =====================================================
         */
        const currentPath =
            resolveRoutePath(
                item.route_path,
                parentPath,
            );


        /**
         * 如果没有 path：
         *
         * 目录一般也不应该生成一个空路由。
         */
        if (!currentPath) {

            console.warn(
                "[Router] 菜单缺少 route_path:",
                item,
            );

            continue;
        }


        /**
         * =====================================================
         * 当前完整路径
         * =====================================================
         */
        const fullPath =
            parentPath
                ? `${parentPath}/${currentPath}`
                : currentPath;


        /**
         * =====================================================
         * 子菜单
         * =====================================================
         *
         * type = 3 的权限节点会在 generateRoutes
         * 内部自动跳过。
         */
        let children:
            AppRouteRecord[] | undefined;


        if (
            Array.isArray(item.children) &&
            item.children.length > 0
        ) {

            const generatedChildren =
                generateRoutes(
                    item.children,
                    fullPath,
                );


            if (
                generatedChildren.length > 0
            ) {

                children =
                    generatedChildren;
            }
        }


        /**
         * =====================================================
         * 是否外链
         * =====================================================
         */
        const isExternal =
            type === 4;


        /**
         * =====================================================
         * 路由组件
         * =====================================================
         *
         * 目录：
         *
         *     RouterView
         *
         * 页面：
         *
         *     实际 vue 页面
         *
         * 外链：
         *
         *     当前先使用 RouterView
         *
         * 后续如果你的外链需要 iframe / 新窗口，
         * 可以单独处理。
         */
     const component =
    loadComponent(
        item.component_path,
    );


        /**
         * =====================================================
         * Vue Router 路由
         * =====================================================
         */
        const route: AppRouteRecord = {

            /**
             * 第一层：
             *
             * /system
             *
             * 子层：
             *
             * user
             */
            path:
                currentPath,


            /**
             * route_name
             */
            name:
                item.route_name ||
                undefined,


            /**
             * 页面组件
             */
            component,


            /**
             * 重定向
             */
            redirect:
                item.redirect ||
                undefined,


            /**
             * 路由元信息
             */
            meta: {

                /**
                 * 标题
                 */
                title:
                    item.title ||
                    item.name ||
                    "",


                /**
                 * 图标
                 */
                icon:
                    item.icon ||
                    "",


                /**
                 * 是否隐藏菜单
                 */
                hidden:
                    item.hidden ??
                    false,


                /**
                 * 是否缓存
                 */
                keepAlive:
                    item.keep_alive ??
                    false,


                /**
                 * 是否始终显示父菜单
                 */
                alwaysShow:
                    item.always_show ??
                    false,


                /**
                 * 是否固定 Tab
                 */
                affix:
                    item.affix ??
                    false,


                /**
                 * 权限标识
                 *
                 * 注意：
                 *
                 * 后端：
                 *
                 * permission
                 *
                 * 前端：
                 *
                 * authMark
                 */
                authMark:
                    item.permission ||
                    undefined,


                /**
                 * 外链标识
                 */
                external:
                    isExternal,


                /**
                 * 菜单类型
                 */
                type,


                /**
                 * 静态壳层
                 */
                shellRoute:
                    item.shell_route ??
                    false,


                /**
                 * query / params
                 * 如果以后需要可以继续使用。
                 */
                params:
                    item.params ??
                    undefined,


                /**
                 * 是否允许 query 变化导致页面重新挂载
                 */
                remountOnFullPath:
                    item.remount_on_full_path ??
                    false,
            },


            /**
             * 子路由
             */
            children,
        };


        /**
         * =====================================================
         * 调试日志
         * =====================================================
         */
        console.log(
            "[Router] 生成路由:",
            {
                type,
                name:
                    route.name,
                path:
                    route.path,
                fullPath,
                componentPath:
                    item.component_path,
                permission:
                    item.permission,
                hidden:
                    item.hidden,
                keepAlive:
                    item.keep_alive,
                children:
                    route.children,
            },
        );


        routes.push(route);
    }


    return routes;
}


/**
 * =========================================================
 * 收集按钮权限
 * =========================================================
 *
 * 后端：
 *
 * type = 3
 *
 * permission：
 *
 *     module_system:menu:create
 *     module_system:menu:update
 *     module_system:menu:delete
 *
 *
 * 最终：
 *
 * authStore.prems
 *
 * [
 *   "module_system:menu:create",
 *   "module_system:menu:update",
 *   "module_system:menu:delete"
 * ]
 */
export function collectPermissions(
    menus: any[],
): string[] {

    const permissionSet =
        new Set<string>();


    /**
     * 递归菜单树
     */
    const walk = (
        items: any[],
    ) => {

        if (!Array.isArray(items)) {
            return;
        }


        for (const item of items) {

            if (!item) {
                continue;
            }


            const type =
                Number(item.type);


            /**
             * 只有 type = 3
             * 才是按钮权限。
             */
            if (
                type === 3 &&
                typeof item.permission === "string"
            ) {

                const permission =
                    item.permission.trim();


                if (permission) {

                    permissionSet.add(
                        permission,
                    );
                }
            }


            /**
             * 继续递归 children
             */
            if (
                Array.isArray(
                    item.children,
                )
            ) {

                walk(
                    item.children,
                );
            }
        }
    };


    walk(menus);


    return Array.from(
        permissionSet,
    );
}


/**
 * =========================================================
 * 添加动态路由
 * =========================================================
 */
export function addDynamicRoutes(
    routes: AppRouteRecord[],
): void {

    /**
     * 已经注册过
     */
    if (hasAddRoute) {
        return;
    }


    /**
     * 防止传入非法数据
     */
    if (!Array.isArray(routes)) {

        console.warn(
            "[Router] 动态路由不是数组:",
            routes,
        );

        return;
    }


    /**
     * =====================================================
     * 注册业务路由
     * =====================================================
     */
    for (const route of routes) {

        /**
         * Vue Router 动态路由必须有 name。
         *
         * 因为后续 resetRouter()
         * 需要通过 name 删除。
         */
        if (!route.name) {

            console.warn(
                "[Router] 动态路由缺少 route_name:",
                route,
            );

            continue;
        }


        const routeName =
            String(route.name);


        /**
         * 已经存在
         */
        if (
            router.hasRoute(
                routeName,
            )
        ) {

            continue;
        }


        /**
         * 添加到 Layout 下面。
         *
         * 最终结构：
         *
         * Layout
         * ├── system
         * │   ├── user
         * │   └── menu
         * └── dashboard
         */
        router.addRoute(
            "Layout",
            route as RouteRecordRaw,
        );


        dynamicRouteNames.push(
            routeName,
        );
    }


    /**
     * =====================================================
     * 添加 404
     * =====================================================
     *
     * 404 必须最后添加。
     */
    addNotFoundRoute();


    /**
     * 标记动态路由已经注册
     */
    hasAddRoute = true;


    console.log(
        "[Router] 动态路由注册完成",
        {
            count:
                dynamicRouteNames.length,
            names:
                dynamicRouteNames,
        },
    );
}


/**
 * =========================================================
 * 添加 404 路由
 * =========================================================
 */
function addNotFoundRoute(): void {

    /**
     * 如果已经存在就不添加。
     */
    if (
        router.hasRoute("any")
    ) {

        return;
    }


    router.addRoute({

        path:
            "/:pathMatch(.*)*",

        name:
            "any",

        redirect:
            "/404",

        meta: {

            title:
                "404",

            hidden:
                true,
        },
    });
}


/**
 * =========================================================
 * 删除动态路由
 * =========================================================
 */
export function resetRouter(): void {

    console.log(
        "[Router] 开始清理动态路由",
    );


    /**
     * =====================================================
     * 删除业务动态路由
     * =====================================================
     */
    for (
        const name
        of dynamicRouteNames
    ) {

        if (
            router.hasRoute(name)
        ) {

            router.removeRoute(
                name,
            );
        }
    }


    /**
     * 清空记录
     */
    dynamicRouteNames.length = 0;


    /**
     * =====================================================
     * 删除 404
     * =====================================================
     */
    if (
        router.hasRoute("any")
    ) {

        router.removeRoute(
            "any",
        );
    }


    /**
     * 重新允许初始化
     */
    hasAddRoute = false;


    console.log(
        "[Router] 动态路由清理完成",
    );
}


/**
 * =========================================================
 * NProgress
 * =========================================================
 */
NProgress.configure({
    showSpinner: false,
});


/**
 * =========================================================
 * 路由守卫
 * =========================================================
 */
router.beforeEach(
    async (
        to: RouteLocationNormalized,
        from: RouteLocationNormalized,
    ) => {

        console.log(
            "========== 路由跳转 ==========",
        );

        console.log(
            "[Router] from:",
            from.fullPath,
        );

        console.log(
            "[Router] to:",
            to.fullPath,
        );

        console.log(
            "[Router] matched:",
            to.matched.map(
                route => ({
                    name:
                        route.name,

                    path:
                        route.path,
                }),
            ),
        );


        /**
         * 开始进度条
         */
        NProgress.start();


        /**
         * 获取用户 Store
         */
        const authStore =
            useAuthStore(
                pinia,
            );


        /**
         * =====================================================
         * Token
         * =====================================================
         *
         * 注意：
         *
         * accessToken 已经持久化到 Pinia。
         *
         * 浏览器刷新以后：
         *
         * authStore.accessToken
         *
         * 依然存在。
         */
      const hasToken =
    Boolean(
        Auth.getAccessToken(),
    );

        /**
         * =====================================================
         * 没有 Token
         * =====================================================
         */
        if (!hasToken) {

            /**
             * 登录页允许进入
             */
            if (
                to.path === "/login"
            ) {

                return true;
            }


            /**
             * 404 允许进入
             */
            if (
                to.path === "/404"
            ) {

                return true;
            }


            /**
             * 其他页面：
             *
             * → 登录页
             */
            return {
                path:
                    "/login",

                query: {

                    redirect:
                        to.fullPath,
                },

                replace:
                    true,
            };
        }


        /**
         * =====================================================
         * 已经有 Token
         * =====================================================
         */


        /**
         * -----------------------------------------------------
         * 登录页
         * -----------------------------------------------------
         */
        if (
            to.path === "/login"
        ) {

            const redirect =
                typeof to.query.redirect === "string"
                    ? to.query.redirect
                    : "";


            /**
             * 有合法 redirect
             */
            if (
                redirect &&
                redirect !== "/login" &&
                !redirect.startsWith(
                    "/login?",
                )
            ) {

                return {
                    path:
                        redirect,

                    replace:
                        true,
                };
            }


            /**
             * 默认进入首页
             */
            return {
                path:
                    "/home",

                replace:
                    true,
            };
        }


        /**
         * =====================================================
         * 根路径
         * =====================================================
         */
        if (
            to.path === "/"
        ) {

            return {
                path:
                    "/home",

                replace:
                    true,
            };
        }


        /**
         * =====================================================
         * 动态路由初始化
         * =====================================================
         *
         * 这里非常重要。
         *
         * 不使用：
         *
         * Object.keys(authStore.info).length
         *
         * 判断是否初始化。
         *
         *
         * 因为：
         *
         * 浏览器刷新后：
         *
         * accessToken
         *     ↓
         *     有
         *
         * info
         *     ↓
         *     有
         *
         * 但是：
         *
         * Vue Router 动态路由
         *     ↓
         *     没有
         *
         *
         * 所以使用：
         *
         * hasGetRoute
         */
        if (
            !authStore.hasGetRoute
        ) {

            try {

                console.log(
                    "[Router] 动态路由未初始化，开始初始化",
                );


                /**
                 * getUserInfo() 内部负责：
                 *
                 * 1. 请求当前用户
                 * 2. 获取后端 menus
                 * 3. generateRoutes()
                 * 4. collectPermissions()
                 * 5. addDynamicRoutes()
                 * 6. 保存 routeList
                 * 7. hasGetRoute = true
                 */
                await authStore.getUserInfo();


                console.log(
                    "[Router] 动态路由初始化完成",
                );


                console.log(
                    "[Router] hasGetRoute:",
                    authStore.hasGetRoute,
                );


                /**
                 * =================================================
                 * 重新匹配当前 URL
                 * =================================================
                 *
                 * 非常重要。
                 *
                 * 例如浏览器直接访问：
                 *
                 * /system/menu
                 *
                 * 第一次导航的时候：
                 *
                 * Router 还不知道 /system/menu。
                 *
                 *
                 * getUserInfo()
                 *     ↓
                 * generateRoutes()
                 *     ↓
                 * addDynamicRoutes()
                 *     ↓
                 * Router 已经知道 /system/menu
                 *
                 *
                 * 所以必须重新导航一次。
                 */
                return {
                    ...to,
                    replace:
                        true,
                };

            } catch (error) {

                console.error(
                    "[Router] 动态路由初始化失败:",
                    error,
                );


                /**
                 * 初始化失败：
                 *
                 * 清理登录状态。
                 *
                 * 注意：
                 *
                 * logout() 默认会自己跳转登录页。
                 */
                try {

                    await authStore.logout();

                } catch (logoutError) {

                    console.error(
                        "[Router] 退出登录失败:",
                        logoutError,
                    );
                }


                /**
                 * 这里不要再重复 push 登录页，
                 * logout() 已经负责处理。
                 */
                return false;
            }
        }


        /**
         * =====================================================
         * 动态路由已经初始化
         * =====================================================
         */


        /**
         * =====================================================
         * 检查路由是否存在
         * =====================================================
         *
         * 注意：
         *
         * 有些情况下 to.matched.length
         * 可能不是你想象的结果。
         *
         * 所以这里只做最终兜底。
         */
        if (
            to.matched.length === 0
        ) {

            console.warn(
                "[Router] 路由没有匹配:",
                to.fullPath,
            );


            return {
                path:
                    "/404",

                replace:
                    true,
            };
        }


        /**
         * =====================================================
         * Tabs
         * =====================================================
         *
         * 隐藏菜单不加入 Tab。
         */
        if (
            to.path !== "/" &&
            to.path !== "/login" &&
            to.path !== "/404" &&
            !to.meta.hidden
        ) {

            const tabsStore =
                useTabsStore(
                    pinia,
                );


            tabsStore.addTab(
                to,
            );
        }


        /**
         * 正常放行
         */
        return true;
    },
);


/**
 * =========================================================
 * afterEach
 * =========================================================
 */
router.afterEach(
    to => {

        /**
         * 关闭进度条
         */
        NProgress.done();


        /**
         * 设置页面标题
         */
        if (
            to.meta?.title
        ) {

            document.title =
                `${setting.title} - ${to.meta.title}`;

        } else {

            document.title =
                setting.title;
        }
    },
);


/**
 * =========================================================
 * 路由异常
 * =========================================================
 */
router.onError(
    error => {

        console.error(
            "[Router] 路由错误:",
            error,
        );


        NProgress.done();
    },
);
