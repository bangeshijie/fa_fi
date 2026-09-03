## 路由的流转

App.vue
└── Layout.vue
    ├── Logo
    ├── MainMenu
    ├── Tabbar
    └── components
        └── RouteView.vue
        └── 动态路由
            ├── type=1 → components/RouteView.vue
            │   └── type=2 → 真实页面.vue
            ├── type=2 → 真实页面.vue
            ├── type=3 → 按钮权限，不生成路由
            └── type=4 → 外链

职责分开：后面再处理 KeepAlive 缓存、Tab 切换、刷新按钮、关闭 Tab、动态路由刷新，就不会互相缠在一起了

Layout.vue：只管布局
layout/components/RouteView.vue：只管页面渲染 / KeepAlive / 刷新
generateRoutes()：只管后端菜单 → Vue Router
tabs.ts：只管 Tab
layoutsetting.ts：只管布局设置

## 权限规则

当前规则：

- 仅本人：只能看自己创建的数据
- 本部门：只能看当前用户所在部门的数据
- 本部门及以下：当前部门及所有下级部门
- 全部：不限制数据范围
- 自定义部门：只能看手动勾选的部门数据

注意：

- 通知、日志、岗位等数据是按照“创建人所属部门”过滤；
- 用户数据按照用户所属部门过滤。
- 菜单、角色、参数、字典等系统配置主要依靠菜单操作权限控制，不使用数据范围。
