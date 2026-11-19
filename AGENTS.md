# FA-FI-MS 项目协作说明

> 本文件是本仓库的项目地图和协作约定，供后续开发者或代码代理使用。
> 其中的路径、命令和行为以当前工作区代码为准；代码发生结构性变化后应同步更新本文件。

## 1. 项目概况

FA-FI-MS 是一个前后端分离的财务运营/后台管理系统，当前包含：

- 后端：Python、FastAPI、SQLAlchemy 2、Pydantic 2、Alembic。
- 前端：Vue 3、TypeScript、Vite、Vue Router、Pinia、Element Plus。
- 数据库：PostgreSQL 18，异步访问使用 `asyncpg`，同步访问和 Alembic 使用 `psycopg`。
- Redis：用于登录会话、验证码、系统配置/字典缓存和操作日志队列，也提供缓存监控页面。
- 文件：后端通过 `/static` 提供静态资源，上传文件保存在 `backend/static/upload`，下载文件目录与上传目录使用独立 Docker 卷。

当前代码按模块组织，主要业务是系统管理和监控管理。根目录同时保留 Docker、Nginx、前端和后端的部署配置。

## 2. 目录结构

```text
fa_fi/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── module_common/       # 通用文件、健康检查
│   │   │   ├── module_dimension/    # 公司、成本中心、会计科目等主数据
│   │   │   ├── module_financial/    # 会计凭证明细、费用分析等财务业务数据
│   │   │   ├── module_budget/       # 预算明细等预算业务数据
│   │   │   ├── module_monitor/      # 在线用户、缓存、资源、服务器监控
│   │   │   └── module_system/       # 认证、用户、部门、角色、菜单等
│   │   ├── common/                  # 常量、枚举、请求/响应约定
│   │   ├── config/                  # Settings、目录路径
│   │   ├── core/                    # 数据库、Redis、CRUD、权限、路由、日志
│   │   ├── scripts/                 # 初始化数据和初始化逻辑
│   │   ├── task/                    # 后台任务，如操作日志消费者
│   │   └── utils/                   # 时间、Excel、上传、密码、IP 等工具
│   ├── alembic/                     # 数据库迁移脚本
│   ├── env/                         # .env.dev、.env.prod、.env.example
│   ├── resource/                    # 后端运行所需资源，如验证码字体
│   ├── static/                      # 静态图片和动态上传目录
│   ├── main.py                      # FastAPI 应用入口
│   ├── pyproject.toml               # Python/uv 依赖
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/api/                     # 按模块划分的 API 封装
│   ├── src/views/                   # 页面组件
│   ├── src/router/                  # 静态路由和动态权限路由
│   ├── src/layout/                  # 后台布局、菜单、标签页、RouteView
│   ├── src/store/                   # Pinia 状态
│   ├── src/components/              # 通用组件
│   ├── src/directives/              # 权限等指令
│   ├── src/utils/                   # 请求、下载、字典、认证等工具
│   ├── .env.development             # 开发环境变量
│   ├── .env.production              # 生产环境变量
│   ├── vite.config.ts
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml               # 当前开发 Compose 配置
├── docker-compose.local.yml         # 当前本地 Compose 配置
├── docker-compose.yml.example       # 示例/生产化 Compose 配置
├── nginx.conf                       # 根域名/生产 Nginx 配置
├── default.conf                     # 另一份 Nginx 配置
└── AGENTS.md
```

## 3. 启动方式和端口

### 3.1 前端开发

在 `frontend` 目录执行：

```bash
pnpm install
pnpm run dev
```

当前 Vite 开发端口是 `5173`。开发环境的 API 前缀是 `/api/v1`，Vite 会将 API 和 `/static` 请求代理到 `VITE_SERVE`，当前开发配置指向后端主机端口 `8002`。

### 3.2 后端开发

在 `backend` 目录执行：

```bash
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

后端代码默认监听容器内 `8000`。直接在本机启动时应从 `backend` 目录使用 `main:app`；旧的 `backend/readme.md` 中的 `app.main:app` 示例与当前入口文件位置不一致。

### 3.3 Docker Compose

常用命令：

```bash
docker compose up --build
docker compose ps
docker compose logs -f backend
docker compose down
```

当前 `docker-compose.yml` 的主机端口映射如下：

| 服务 | 容器端口 | 主机端口 | 说明 |
| --- | ---: | ---: | --- |
| 前端开发服务器 | 5173 | 5173 | 通常由 `pnpm run dev` 单独启动 |
| backend | 8000 | 8002 | 开发 Compose 配置 |
| PostgreSQL | 5432 | 5433 | 仅绑定本机回环地址 |
| Redis | 6379 | 6380 | 仅绑定本机回环地址 |

因此，前端开发时请求配置使用后端的 `8002`；后端进程自身仍监听 `8000`。`docker-compose.yml.example` 的生产示例把 backend 映射为主机 `8000:8000`，不要把两种映射混淆。

当前根目录 Compose 文件只编排 PostgreSQL、Redis、Alembic 迁移服务和 backend，没有编排 frontend。前端生产镜像使用 Nginx，需单独构建/部署或由外部编排文件接入。

## 4. 后端应用和 API 结构

`backend/main.py` 创建 FastAPI 应用，并注册：

- 健康检查：`/api/v1/common/health`、`/api/v1/common/health/live`、`/api/v1/common/health/ready`。
- 通用路由：`/api/v1/common/file`、`/api/v1/common/health`。
- 主数据路由：`/api/v1/dimension/company`、`/api/v1/dimension/cost-center`、`/api/v1/dimension/accounting-subject`，公司、成本中心、会计科目等主数据统一放在 `module_dimension`。
- 财务路由：`/api/v1/financial/accounting-voucher-detail`、`/api/v1/financial/expense-analysis`；预算路由：`/api/v1/budget/budget-detail`。`module_financial` 与 `module_budget` 均和 `module_dimension` 平行。
- 系统路由：`/api/v1/system/...`。
- 监控路由：`/api/v1/monitor/...`。

系统模块包括：

- `auth`：登录、刷新 Token、退出、验证码、OAuth。
- `user`：用户查询、创建、修改、删除、导入、导出。
- `dept`：部门树和部门 CRUD。
- `role`：角色 CRUD、菜单权限、数据权限。
- `menu`：目录、页面、按钮权限、外链菜单。
- `dict`：字典类型和字典数据。
- `log`：操作/登录日志。
- `notice`：公告通知。
- `param`：系统参数。
- `position`：岗位。

监控模块包括：

- `online`：在线会话、强制下线。
- `cache`：Redis 信息、缓存名称、键和值、清理操作。
- `resource`：`static/upload` 下的目录和文件管理。
- `server`：CPU、内存、磁盘、运行时间和 Python 进程资源。

响应统一使用 `ResponseSchema`，主要字段为 `code`、`msg`、`data`、`status_code`、`success`。普通成功响应使用 `SuccessResponse`；文件流使用 `StreamResponse` 或 `UploadFileResponse`，不能按 JSON 响应处理。

## 5. 数据库和 Alembic

### 5.1 PostgreSQL

当前数据库配置已经切换为 PostgreSQL：

- Docker 镜像：`postgres:18`。
- 数据库名：`fa_fi_pgdb`。
- 用户名：`postgres`。
- 容器内主机名：`postgres`，端口 `5432`。
- 主机开发访问：`127.0.0.1:5433`。
- 应用异步连接：`postgresql+asyncpg://...`。
- 应用同步/Alembic 连接：`postgresql+psycopg://...`。

密码、JWT 密钥、OAuth 密钥等敏感值只能通过 `backend/env/.env.dev`、`backend/env/.env.prod` 或部署平台注入，禁止写入本文件、提交到 Git 或在日志中打印。

### 5.2 独立卷

Compose 当前使用以下独立卷：

- `postgres18-data`：PostgreSQL 数据。
- `redis-data`：Redis AOF 数据。
- `upload-data`：`/code/static/upload`，用户上传和资源管理文件。
- `download-data`：`/code/static/download`，与上传目录隔离。

PostgreSQL 18 的 Compose 挂载目标是 `/var/lib/postgresql`，配置注释说明 PGDATA 位于 PostgreSQL 18 镜像对应的子目录。不要随意把数据库卷改成容器临时目录。

### 5.3 迁移流程

`backend/alembic/env.py`：

- 从项目 `settings.DB_URI` 读取数据库地址，`alembic.ini` 中的 `sqlalchemy.url` 留空是有意设计。
- 显式导入现有 ORM 模型，作为 `MappedBase.metadata` 的迁移目标。
- 开启类型和服务端默认值比较。
- PostgreSQL 连接使用 `settings.TIMEZONE` 设置会话时区。

Compose 启动时先运行独立的 `alembic-migration` 服务：

```bash
cd backend
uv run alembic upgrade head
uv run alembic current
uv run alembic history
uv run alembic revision --autogenerate -m "变更说明"
```

当前迁移版本目录至少包含初始 PostgreSQL schema 和北京时间迁移。新增或修改模型时先生成迁移并检查生成结果，再执行升级；不要依赖生产启动时直接 `create_all` 替代迁移。

应用启动生命周期中的 `InitializeData().init_db()` 只负责在空表时导入 `backend/app/scripts/data/*.json` 基础数据，表结构由 Compose 的 Alembic 迁移服务负责。

## 6. 时间和时区

项目业务时区统一为 `Asia/Shanghai`（北京时间，UTC+8）：

- Settings 中的 `TIMEZONE` 是 `Asia/Shanghai`。
- Docker、PostgreSQL 会话和 Alembic 配置均按北京时间处理；Nginx 只负责反向代理，不负责业务时间生成。
- `backend/app/utils/time_util.py` 提供 `now_beijing()` 和 `now_beijing_naive()`。
- 基础时间戳字段使用 `now_beijing_naive()`，兼容当前无时区的数据库 timestamp 字段。
- 用户 `last_login` 等明确带时区的字段使用带时区时间。
- Loguru 控制台和文件日志在格式化时转换为北京时间。
- Excel 导出前由 `ExcelUtil` 去掉 `datetime` 的 `tzinfo`，因为 Excel 不保存时区信息，但保留北京时间的时钟值。

新增业务时间字段时，必须先确认数据库列是 `timestamp without time zone` 还是 `timestamptz`，不要混用 naive 和 aware datetime。接口展示格式由 `backend/app/common/constant.py` 和响应编码器统一处理。

## 7. 认证、密码、IP 和操作日志

- 登录和接口认证使用 JWT；Access Token 和 Refresh Token 的会话状态存放在 Redis。
- Redis 会校验当前请求 Token 与会话键中的 Token 是否完全一致，因此退出登录和刷新后旧 Token 可以立即失效。
- 密码由密码工具进行哈希处理，业务日志不得记录明文密码。
- `backend/app/core/router_class.py` 中的 `OperationLogRoute` 在响应后记录操作日志，并对密码、Token、secret 等字段递归脱敏。
- 请求 IP 会优先读取代理头，再回退到连接地址，并使用 `ipaddress` 校验；要正确部署在 Nginx 后面，需保留 `X-Real-IP`、`X-Forwarded-For` 等代理头。
- 登录场景会尝试解析 IP 归属地；其他操作日志由 `operation_log_worker` 异步补充归属地，归属地服务不可用不能阻断业务响应。
- IP 归属地由 `IP_LOCATION_ENABLE` 开关控制，并受外部 HTTP 默认超时限制。

新增接口时，如果需要写操作日志，应使用已有模块的 `APIRouter(route_class=OperationLogRoute, ...)`；文件流接口需要确认日志路由不会误读文件响应体。

## 8. Redis 使用约定

Redis 内置键名集中在 `backend/app/common/enums.py` 的 `RedisInitKeyConfig`，当前主要命名空间包括：

- Access Token、Refresh Token。
- 图片验证码。
- `system_config`：系统参数缓存。
- `system_dict`：按字典类型缓存的字典数据。
- 操作日志队列 `operation_log_queue`。

当前缓存策略：

1. 应用启动时从 PostgreSQL 初始化系统参数和启用字典到 Redis。
2. 业务读取字典时优先查 Redis，未命中或无效时回源 PostgreSQL，并按配置写回缓存。
3. 字典、参数新增/修改/删除后应清理对应缓存，避免旧数据继续被使用。
4. 用户列表、用户导出行数据不走 Redis 缓存；用户导出虽然接收 Redis 依赖，但 Redis 只用于动态读取性别字典映射。
5. 缓存监控使用 `SCAN`，不要在生产代码中用无边界的 `KEYS` 阻塞 Redis。

Redis 配置在容器内应使用服务名 `redis` 和容器端口 `6379`；只有本机直连时才使用 Compose 映射端口 `6380`。开发和生产环境都应显式配置密码策略，不要依赖代码中的默认空密码。

## 9. 权限模型

### 9.1 菜单权限和页面路由

菜单数据在后端 `sys_menu` 表和初始化 JSON 中维护，菜单类型约定：

- `type = 1`：目录。
- `type = 2`：页面菜单。
- `type = 3`：按钮/接口权限，不生成前端路由。
- `type = 4`：外链。

前端 `frontend/src/router/permission.ts`：

1. 获取当前用户信息和后端菜单树。
2. 使用 `import.meta.glob('/src/views/**/*.vue')` 扫描页面。
3. 将菜单的 `component_path` 映射为 `src/views/<component_path>.vue`。
4. 目录节点没有页面组件时使用 `src/layout/components/RouteView.vue` 承载子页面。
5. 收集 `type = 3` 的 `permission` 到 Pinia 权限状态。
6. 将动态路由挂到名为 `Layout` 的静态路由下，并在退出时移除。

因此，页面文件应放在 `frontend/src/views` 下，并且路径必须与后端 `component_path` 一致。`RouteView.vue` 位于 `frontend/src/layout/components/RouteView.vue` 是合理位置，职责是承载目录型嵌套路由，不应移动到业务页面目录。

前端页面上的按钮使用 `v-permission` 等权限指令；后端接口必须同时使用 `AuthPermission([...])` 做最终校验，不能只依赖前端隐藏按钮。

### 9.2 后端权限判断

`AuthPermission` 的权限集合判断是“满足任意一个声明权限即可”。当前大多数接口每个只声明一个权限标识，例如：

```text
module_system:user:query
module_system:user:create
module_system:user:update
module_system:user:delete
```

角色授权保存时，`RoleCRUD.set_role_menus_crud()` 会把已选菜单的父目录一并补齐，保证页面路由可以生成；按钮权限可以部分选择。页面是否显示由后端返回的可见菜单树决定，接口能否执行由后端具体权限标识决定，两者都不能只看前端状态。

### 9.3 数据范围

角色 `data_scope` 约定：

| 值 | 含义 |
| ---: | --- |
| 1 | 仅本人 |
| 2 | 本部门 |
| 3 | 本部门及以下 |
| 4 | 全部 |
| 5 | 自定义部门 |

“自定义”不是自定义 SQL，而是把角色与手动勾选的部门写入 `sys_role_depts`；只有 `data_scope = 5` 时这些关联部门参与过滤。多个角色的数据范围按并集处理；存在“全部”时优先放开范围；没有有效角色时，普通数据默认只能看本人数据。

数据过滤由 `backend/app/core/permission.py` 和 `CRUDBase` 共同完成，并按模型策略区分：

- `DeptModel`：部门关联策略。
- `UserModel`：按用户所属部门过滤。
- `RoleModel`：按当前用户角色关联。
- 其他带 `created_id` 的业务模型：按创建人的部门或本人过滤。
- 菜单、角色、参数、字典等系统配置主要依靠菜单操作权限，不应擅自套用业务数据范围。

## 10. 用户管理、导入和导出

- 用户性别选项来自字典类型 `sys_user_sex`，优先 Redis、失效时回源数据库，业务代码不维护固定性别映射。
- 用户导出接口接收分页对象主要为了复用排序参数，实际调用 `get_user_list_service()`，不传 `page_no/page_size`，因此导出的是“当前查询条件匹配的全部用户”，不是当前页。
- 用户导出仍会使用 Redis 中的性别字典做标签转换，但不缓存用户列表本身。
- Excel 日期导出经过统一的无时区处理，避免 `Excel does not support datetimes with timezones`。
- 用户导入文件格式错误、表头缺失或文件为空会返回 4xx；逐行数据使用 SAVEPOINT，单行失败不会回滚其他成功行。
- 导入结果包含总数、成功数、新增数、更新数、重复数、失败数和失败明细；成功数为零时返回 422，部分成功时以 200 返回带失败明细的结果。
- 当前导入模板字段为：部门编号、账号、昵称、邮箱、手机号、性别、状态。部门字段当前仍按部门编号读取；修改导入字段前要同步模板、解析、校验、前端结果展示和接口文档。

## 11. 文件和资源管理

通用文件接口：

- `POST /api/v1/common/file/upload`：按 `upload_type` 支持通用文件、头像、参数文件和资源文件。
- `POST /api/v1/common/file/download`：按文件路径返回下载响应。
- 头像上传允许登录用户使用，其他通用文件操作仍需相应菜单权限。

监控资源管理页面对应 `module_monitor/resource`，当前安全边界是只管理 `backend/static/upload`：

- 支持目录浏览、上传、下载、删除、移动、复制、重命名、创建目录和导出。
- 对路径做规范化、路径遍历和目录深度检查。
- Compose 中的 `download-data` 是独立卷，但资源管理服务当前不会把 `static/download` 作为浏览根目录。
- 因此页面显示的是 upload 资源管理，不等于系统所有磁盘文件管理。

新增下载能力时应复用现有安全路径校验，不能直接把用户传入路径交给 `FileResponse`；同时要检查是否需要新增权限标识和前端 API 类型。

## 12. 前端页面和 API 约定

- 页面按 `src/views/module_system/<模块>`、`src/views/module_monitor/<模块>`、`src/views/module_dimension/<模块>`、`src/views/module_financial/<模块>` 或 `src/views/module_budget/<模块>` 组织。
- API 按同样的模块边界放在 `src/api/module_system`、`src/api/module_monitor`、`src/api/module_dimension`、`src/api/module_financial`、`src/api/module_budget`。
- 查询页面通常维护 `page_no`、`page_size` 和查询条件；导出接口若设计为全部导出，应明确传递筛选条件，不要把分页参数误当成导出范围。
- 时间、下载、响应错误处理应复用 `src/utils`，不要在每个页面重新实现 Token、文件名解析或错误提示。
- 当前监控页面包括 `cache/index.vue`、`online/index.vue`、`resource/index.vue`、`server/index.vue`，风格使用 Element Plus 卡片/表格和项目 CSS 变量。
- 页面权限指令只负责 UI 体验，后端接口权限才是安全边界。

## 13. 验证命令

前端修改后至少执行：

```bash
cd frontend
npx vue-tsc -b --pretty false
pnpm run build
```

当前 `package.json` 的 build 脚本包含 `vite build --configLoader native`，这是为了兼容当前 Vite 配置加载方式。构建可能出现大 chunk、动态/静态导入提示或空图表 chunk 警告；先区分 warning 与真正的类型/构建失败。

后端修改后优先在 Docker 或可用的 Python 3.14 环境验证：

```bash
cd backend
uv run python -m compileall app main.py
uv run alembic check
uv run alembic upgrade head
```

当前工作区本机曾出现 `.venv/pyvenv.cfg` 指向不存在的 Python 3.14 安装路径，导致本地 Python/uv 验证可能失败；这属于环境问题，不能据此断言后端代码已通过运行时测试。Docker 构建环境使用 `python:3.14-slim`。

通用检查：

```bash
git diff --check
git status --short
```

## 14. 修改纪律和排障顺序

1. 修改前先查看 `git status --short` 和相关文件 diff，当前工作区可能包含用户已有的未提交文件。
2. 只修改本次需求涉及的文件，不使用 `git reset --hard`、`git checkout --` 或宽范围删除命令覆盖用户改动。
3. 配置优先走环境变量；任何密码、Token、JWT 密钥、OAuth 密钥、生产域名凭据不得写入日志、示例输出或本文件。
4. 后端问题按“路由注册 → 认证/权限 → Service → CRUD/Permission → 数据库/Redis”顺序排查。
5. 前端问题按“页面路径/component_path → 动态路由 → API 请求 → 响应结构 → 权限指令”顺序排查。
6. 数据库问题先确认 Compose 服务健康、连接主机/端口和 Alembic 版本，再检查模型与迁移是否一致。
7. Redis 问题先确认容器连接和 `ping`，再检查命名空间、TTL、缓存失效和数据库回源逻辑。
8. 涉及时间的问题同时检查 Python 时区、数据库会话时区、ORM 列类型、JSON 序列化和 Excel 导出，不要只改显示层。

## 15. 当前已知注意事项

- `docker-compose.yml` 的 backend 主机端口是 `8002`，生产示例是 `8000`；前端开发端口是 `5173`。
- Compose 的迁移服务完成后 backend 才启动；迁移失败时 backend 会因依赖条件不满足而不启动。
- `backend/readme.md` 的启动入口示例需要以当前 `backend/main.py` 为准。
- `backend/app/config/setting.py` 和环境文件都存在默认值/开发值，部署生产环境时必须用环境变量覆盖敏感配置，并关闭不必要的 DEBUG/外部 IP 归属地请求。
- `resource` 页面只浏览 `static/upload`；独立的 `static/download` 卷不代表它会自动出现在资源树中。
- 用户导出是按筛选条件导出全部匹配数据，分页对象中的页码和每页条数不会限制导出范围。
- 所有新页面必须确认后端菜单的 `component_path`、`route_path`、`route_name` 和权限节点同步，否则动态路由可能落到 404 或页面没有按钮权限。
