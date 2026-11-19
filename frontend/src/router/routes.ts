import type { RouteRecordRaw } from 'vue-router'

/**
 * 不依赖后端权限的固定菜单路由。
 *
 * Home 是登录后的基础入口，即使当前用户没有配置任何业务菜单，
 * 也必须可以访问；因此它既注册到 Layout，也提供给侧边栏使用。
 */
export const constantMenuRoutes: RouteRecordRaw[] = [
    {
        path: 'home',
        name: 'Home',
        component: () =>
            import('@/views/home/index.vue'),
        meta: {
            title: '首页',
            icon: 'HomeFilled',
            hidden: false,
            affix: true,
        },
    },
    {
        path: 'about',
        name: 'About',
        component: () =>
            import('@/views/about/index.vue'),
        meta: {
            title: '关于',
            icon: 'InfoFilled',
            hidden: false,
        },
    },
]

/**
 * 静态路由
 *
 * Layout 是整个后台系统的页面框架。
 *
 * 动态业务路由都会挂到 Layout 下面。
 */
export const constantRoutes: RouteRecordRaw[] = [

    /**
     * 登录页
     */
    {
        path: '/login',
        name: 'Login',
        component: () =>
            import('@/views/login/index.vue'),

        meta: {
            title: '登录',
            hidden: true,
        },
    },

    /**
     * 后台 Layout
     *
     * 动态路由全部挂到这里。
     */
    {
        path: '/',
        name: 'Layout',
        component: () =>
            import('@/layout/index.vue'),

        children: [
            ...constantMenuRoutes,
            {
                path: 'profile',
                name: 'Profile',
                component: () =>
                    import('@/views/profile/index.vue'),
                meta: {
                    title: '个人中心',
                    hidden: true,
                },
            },
        ],
    },

    /**
     * 404
     */
    {
        path: '/404',
        name: '404',
        component: () =>
            import('@/views/404/index.vue'),

        meta: {
            title: '404',
            hidden: true,
        },
    },
]


/**
 * 任意未知路由
 *
 * 注意：
 * 必须最后动态添加。
 */
export const anyRoutes: RouteRecordRaw[] = [

    {
        path: '/:pathMatch(.*)*',
        name: 'any',

        redirect: '/404',

        meta: {
            title: '404',
            hidden: true,
        },
    },

]
