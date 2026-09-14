# FA-FI-MS 生产部署

生产环境采用宿主机 Nginx 提供前端静态文件，Docker Compose 运行 PostgreSQL、Redis、Alembic migration 和后端。

## 首次部署

服务器目录固定为 `/opt/fa_fi`，前端版本目录为 `/opt/fa_fi/frontend-releases`，Nginx 使用 `/opt/fa_fi/frontend-current` 软链接。

服务器首次准备环境文件：

```bash
mkdir -p /opt/fa_fi/backend/env /opt/fa_fi/frontend-releases
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
curl -fsS http://127.0.0.1:8002/api/v1/common/health
```

旧测试项目确认无保留需求后，只在旧项目目录执行：

```bash
docker compose down --volumes --remove-orphans
```

不要对新项目执行 `down --volumes`。

## 本地访问数据库和 Redis

PostgreSQL 和 Redis 只绑定云服务器的 `127.0.0.1`，不会直接暴露到公网。本地电脑需要保持 SSH 隧道打开：

```bash
ssh -N \
  -L 15432:127.0.0.1:5432 \
  -L 16379:127.0.0.1:6379 \
  susan@<服务器IP>
```

本地客户端连接 PostgreSQL 时使用 `127.0.0.1:15432`，连接 Redis 时使用 `127.0.0.1:16379`。数据库名、用户名和密码读取服务器上的 `backend/env/.env.prod`；Redis 还需要填写 `REDIS_PASSWORD`。

如果本地 5432 或 6379 端口没有冲突，也可以将 SSH 隧道的本地端口改成同名端口。

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
mkdir -p /opt/fa_fi/frontend-releases/<commit-id>
# 将 dist 上传到 /opt/fa_fi/frontend-releases/<commit-id>/dist
ln -sfn /opt/fa_fi/frontend-releases/<commit-id>/dist /opt/fa_fi/frontend-current
```

## Nginx 和证书

你已有证书时不需要 Certbot。将证书文件和私钥文件放到固定目录，并确保权限正确：

```bash
mkdir -p /etc/nginx/ssl/fa_fi
cp <你的证书文件> /etc/nginx/ssl/fa_fi/fullchain.pem
cp <你的私钥文件> /etc/nginx/ssl/fa_fi/privkey.pem
chmod 600 /etc/nginx/ssl/fa_fi/privkey.pem
```

证书必须覆盖 `chyichyi.com` 和 `www.chyichyi.com`。将 `deploy/nginx/fa_fi.conf` 安装到 `/etc/nginx/conf.d/`；证书不存在时才使用 `fa_fi-http.conf` 作为临时 HTTP 配置：

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
