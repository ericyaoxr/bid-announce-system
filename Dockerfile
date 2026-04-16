# ===== 构建阶段 =====
FROM python:3.11-slim AS builder

WORKDIR /build

# 复制项目文件
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY scripts/ ./scripts/

# 安装依赖到独立目录
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install . && \
    pip install --no-cache-dir --prefix=/install fastapi uvicorn openpyxl

# ===== 运行阶段 =====
FROM python:3.11-slim

LABEL maintainer="Development Team"
LABEL description="中标结果公示系统 - 数据采集与展示"

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# 从构建阶段复制已安装的包
COPY --from=builder /install/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /install/bin /usr/local/bin

# 复制项目文件
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY web/ ./web/
COPY pyproject.toml ./

# 创建数据目录并设置权限
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8000

# 数据库挂载点
VOLUME ["/app/data"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/dashboard')" || exit 1

# 启动命令
CMD ["python", "scripts/start_server.py", "--host", "0.0.0.0", "--port", "8000", "--no-browser"]
