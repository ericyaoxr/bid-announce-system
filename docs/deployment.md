# 部署指南

## Docker Compose 部署（推荐）

最简单的部署方式，一条命令启动所有服务。

### 前置条件

- Docker 20.10+
- Docker Compose V2（`docker compose` 命令，非旧版 `docker-compose`）

### 快速启动

```bash
# 克隆项目
git clone https://github.com/ericyaoxr/bid-announce-system.git
cd bid-announce-system

# 一键启动
docker compose up -d

# 查看运行状态
docker compose ps

# 查看日志
docker compose logs -f bid-announce
```

启动后访问：
- 前端：http://localhost:8000/web/
- API 文档：http://localhost:8000/docs
- Dashboard：http://localhost:8000/api/dashboard

### 常用操作

```bash
# 停止服务
docker compose down

# 重启服务
docker compose restart

# 更新到最新镜像
docker compose pull && docker compose up -d

# 查看实时日志
docker compose logs -f

# 进入容器
docker compose exec bid-announce bash
```

### 自定义配置

通过环境变量或修改 `docker-compose.yml` 进行配置：

```bash
# 自定义端口（默认 8000）
PORT=9000 docker compose up -d
```

也可直接编辑 `docker-compose.yml`：

```yaml
ports:
  - "9000:8000"   # 将宿主机端口改为 9000

volumes:
  - /your/data/path:/app/data   # 自定义数据存储路径
```

### 数据持久化

数据默认存储在项目目录下的 `./data` 目录，通过 volume 映射到容器内 `/app/data`。SQLite 数据库文件位于此目录中，容器重建不会丢失数据。

建议定期备份 `data/` 目录：

```bash
# 备份
cp -r data/ data_backup_$(date +%Y%m%d)/

# 或使用 tar
tar czf data_backup_$(date +%Y%m%d).tar.gz data/
```

### 本地构建

默认从 ghcr.io 拉取预构建镜像。如需本地构建，编辑 `docker-compose.yml`：

```yaml
services:
  bid-announce:
    # 注释掉 image 行
    # image: ghcr.io/ericyaoxr/bid-announce-system:latest
    build: .
```

然后运行：

```bash
docker compose up -d --build
```

---

## Docker 手动部署

### 从 ghcr.io 拉取

```bash
# 登录 GitHub Container Registry
docker login ghcr.io -u YOUR_USERNAME

# 拉取镜像
docker pull ghcr.io/ericyaoxr/bid-announce-system:latest

# 运行
docker run -d \
  --name bid-announce \
  --restart unless-stopped \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  ghcr.io/ericyaoxr/bid-announce-system:latest
```

### 本地构建

```bash
# 构建镜像
docker build -t bid-announce-system .

# 运行容器
docker run -d \
  --name bid-announce \
  --restart unless-stopped \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  bid-announce-system
```

### 常用命令

```bash
# 查看日志
docker logs -f bid-announce

# 停止容器
docker stop bid-announce

# 删除容器
docker rm bid-announce

# 重启容器
docker restart bid-announce

# 进入容器
docker exec -it bid-announce bash
```

---

## 镜像标签说明

| 标签 | 说明 | 更新策略 |
|------|------|----------|
| `latest` | 最新稳定版 | 每次 push 到 main 分支自动构建 |
| `main` | main 分支最新构建 | 每次 push 到 main 分支自动构建 |
| `1.0.0` | 语义化版本 | 对应 git tag `v1.0.0` |

---

## 健康检查

容器内置健康检查，每 30 秒检测一次：

```bash
# 查看健康状态
docker inspect --format='{{.State.Health.Status}}' bid-announce

# 或使用 docker compose
docker compose ps
```

健康状态说明：
- `healthy` — 服务正常运行
- `starting` — 服务启动中（最多 15 秒）
- `unhealthy` — 服务异常，检查日志排查

---

## 反向代理部署

生产环境建议使用 Nginx 反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

配合 docker-compose 使用时，确保端口映射与 Nginx 配置一致。
