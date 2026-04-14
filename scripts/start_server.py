"""启动后端API服务器v2（深度数据+前端静态文件）"""
from __future__ import annotations

import argparse
import webbrowser
from pathlib import Path

import uvicorn
from fastapi.staticfiles import StaticFiles

from src.api.app_v2 import app


def main():
    parser = argparse.ArgumentParser(description="中标结果公示系统 - Web服务")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=8000, help="监听端口")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    args = parser.parse_args()

    # 挂载前端静态文件
    web_dir = Path(__file__).parent.parent / "web"
    if web_dir.exists():
        app.mount("/web", StaticFiles(directory=str(web_dir), html=True), name="web")

    url = f"http://localhost:{args.port}"
    print(f"\n{'='*50}")
    print(f"  中标结果公示系统 v2.0")
    print(f"  前端地址: {url}/web/")
    print(f"  API文档:  {url}/docs")
    print(f"{'='*50}\n")

    if not args.no_browser:
        webbrowser.open(f"{url}/web/")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
