# syntax=docker/dockerfile:1

# 阶段1: 前端构建（仅在未提供预构建产物时执行）
FROM node:22-slim AS frontend-builder

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# 阶段2: Python 依赖构建
FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY scripts/ ./scripts/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install .

# 阶段3: 最终运行镜像
FROM python:3.11-slim

LABEL maintainer="Development Team"
LABEL description="中标结果公示系统 v3.0 - 数据采集与展示"

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

COPY --from=builder /install/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /install/bin /usr/local/bin

COPY src/ ./src/
COPY scripts/ ./scripts/
COPY pyproject.toml ./

# 优先使用 CI 预构建的前端产物，否则使用 frontend-builder 阶段构建的
COPY --from=frontend-builder /build/frontend/dist ./web/
COPY web/ ./web/

RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

VOLUME ["/app/data"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["python", "scripts/start_server.py", "--host", "0.0.0.0", "--port", "8000", "--no-browser"]
