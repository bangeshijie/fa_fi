# FA-FI-MS 生产部署

生产环境采用宿主机 Nginx 提供前端静态文件，Docker Compose 运行 PostgreSQL、Redis、Alembic migration 和后端。

## 首次部署

服务器目录固定为 `/opt/fa_fi_ms`，前端版本目录为 `/opt/fa_fi_ms/frontend-releases`，Nginx 使用 `/opt/fa_fi_ms/frontend-current` 软链接。

服务器首次准备环境文件：

```bash
mkdir -p /opt/fa_fi_ms/backend/env /opt/fa_fi_ms/frontend-releases
cp deploy/backend/.env.prod.example backend/env/.env.prod
chmod 600 backend/env/.env.prod
```

编辑 `backend/env/.env.prod`，至少替换数据库密码、Redis 密码和 `SECRET_KEY`，并保证 `DATABASE_PASSWORD` 与 `POSTGRES_PASSWORD` 相同。

检查并启动后端栈：

```bash
docker compose -f docker-compose.prod.yml config
docker compose -f docker-compose.prod.yml up -d postgres redis
docker compose -f docker-compose.prod.yml run --rm alembic-migration
docker compose -f docker-compose.prod.yml up -d backend
docker compose -f docker-compose.prod.yml ps
curl -fsS http://127.0.0.1:8002/health
```

旧测试项目确认无保留需求后，只在旧项目目录执行：

```bash
docker compose down --volumes --remove-orphans
```

不要对新项目执行 `down --volumes`。

## 发布前端

在本地或构建机使用仓库根目录的 `.nvmrc` 和 `frontend/package.json` 中固定的 pnpm 版本：

```bash
cd frontend
corepack enable
pnpm install --frozen-lockfile
pnpm run build
```

将 `frontend/dist` 上传到服务器的全新版本目录，然后原子切换：

```bash
mkdir -p /opt/fa_fi_ms/frontend-releases/<commit-id>
# 将 dist 上传到 /opt/fa_fi_ms/frontend-releases/<commit-id>/dist
ln -sfn /opt/fa_fi_ms/frontend-releases/<commit-id>/dist /opt/fa_fi_ms/frontend-current
```

## Nginx 和证书

安装 `deploy/nginx/fa_fi_ms.conf` 到 `/etc/nginx/conf.d/`。如果证书不存在，先使用 HTTP 临时配置申请包含根域名和 www 域名的证书：

```bash
certbot --nginx -d chyichyi.com -d www.chyichyi.com
```

完成后检查并 reload：

```bash
nginx -t
systemctl reload nginx
```

## 后续更新

```bash
git pull --ff-only origin master
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml run --rm alembic-migration
docker compose -f docker-compose.prod.yml up -d backend
```

前端始终先在构建机生成完整 `dist`，上传后再切换 `frontend-current`。回滚时切回上一个前端版本目录；后端回到上一 Git commit 后重新构建并启动。
