# 中标结果公示系统

从采购平台采集结果公示数据，含中标人、金额、联系人等深度信息的自动化系统。

## 功能特性

### 数据采集
- **增量采集** — 仅抓取结果公示新增数据，遇到已有数据自动停止
- **按时间采集** — 抓取最近 N 天的结果公示数据
- **全量采集** — 从第1页逐页抓取全部结果公示数据
- **补采详情** — 对未获取详情的记录补充抓取
- 所有模式仅保留有中标人的数据

### 数据展示
- **Dashboard** — 中标数最多公司 TOP10、中标总金额最高公司 TOP10
- **列表** — 按中标人展开显示，支持公告标题/招标人/中标人模糊搜索
- **详情** — 完整公告信息弹窗展示
- **分页** — 支持 10/20/50/100 条每页切换

### 数据导出
- **Excel** — 带样式（蓝色表头、金额红色加粗、自动筛选、冻结首行）
- **CSV** — UTF-8 BOM，Excel 可直接打开
- 按中标人展开导出，每个中标人一行

### 系统特性
- 采集任务后台异步执行，实时日志 + 进度条
- 深度数据库 SQLite，零外部依赖

## 项目结构

```
project/
├── src/
│   ├── api/             # FastAPI 后端 (app_v2.py)
│   ├── config/          # 配置模块
│   ├── core/            # 核心模块
│   ├── crawlers/        # 采集数据实现 (deep_crawler.py)
│   ├── models/          # 数据模型
│   ├── pipelines/       # 数据处理管道
│   └── utils/           # 工具函数
├── web/
│   └── index.html       # 纯HTML前端（零CDN依赖）
├── scripts/
│   ├── start_server.py  # Web服务启动
│   ├── run_deep_crawler.py  # 采集数据启动
│   └── init_db.py       # 数据库初始化
├── tests/               # 测试目录
├── docs/                # 文档
├── Dockerfile           # Docker构建
└── pyproject.toml       # 项目配置
```

## 环境要求

- Python 3.11+

## 快速开始

### 本地运行

```bash
# 安装依赖
pip install -e .

# 启动Web服务
python scripts/start_server.py --host 0.0.0.0 --port 8000

# 启动采集数据（命令行）
python scripts/run_deep_crawler.py --mode incremental --pages 10
```

### Docker 运行

```bash
# 构建镜像
docker build -t bid-announce-system .

# 运行容器
docker run -d \
  --name bid-announce \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  bid-announce-system

# 访问
# 前端: http://localhost:8000/web/
# API:  http://localhost:8000/docs
```

### ghcr.io 部署

```bash
# 登录
docker login ghcr.io -u YOUR_USERNAME

# 拉取
docker pull ghcr.io/YOUR_USERNAME/bid-announce-system:latest

# 运行
docker run -d -p 8000:8000 -v ./data:/app/data ghcr.io/YOUR_USERNAME/bid-announce-system:latest
```

## API 文档

启动服务后访问 `http://localhost:8000/docs` 查看完整 API 文档。

### 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/dashboard` | Dashboard 统计数据 |
| GET | `/api/announcements` | 公告列表（支持分页/搜索/筛选） |
| GET | `/api/announcements/{id}` | 公告详情 |
| POST | `/api/crawler/start` | 启动采集任务 |
| POST | `/api/crawler/stop` | 停止采集任务 |
| GET | `/api/crawler/status` | 采集任务状态 + 实时日志 |
| GET | `/api/export/excel` | 导出 Excel |
| GET | `/api/export/csv` | 导出 CSV |

### 查询参数

| 参数 | 说明 | 示例 |
|------|------|------|
| keyword | 搜索公告标题/招标人/中标人 | `?keyword=路桥建设` |
| category | 按分类筛选 | `?category=工程` |
| tender_mode | 按招标方式筛选 | `?tender_mode=公开招标` |
| page | 页码 | `?page=1` |
| size | 每页条数 | `?size=20` |

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 代码检查
ruff check .

# 代码格式化
ruff format .

# 类型检查
mypy src/

# 运行测试
pytest tests/ -v

# 测试覆盖率
pytest --cov=src tests/
```

## CI/CD

- **CI** (`.github/workflows/ci.yml`) — ruff + mypy + pytest + bandit
- **Docker** (`.github/workflows/docker-build-push.yml`) — 构建 + 推送 ghcr.io
  - push main → `latest` 标签
  - push tag v* → 版本号标签 (如 `1.0.0`)
  - 手动触发 → 可选 `latest`

## 许可

MIT License
