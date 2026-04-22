from __future__ import annotations

import argparse
import webbrowser

import uvicorn

from src.api.app import app


def main():
    parser = argparse.ArgumentParser(description="中标结果公示系统 - Web服务")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=8000, help="监听端口")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    args = parser.parse_args()

    url = f"http://localhost:{args.port}"
    print(f"\n{'=' * 50}")
    print("  中标结果公示系统 v3.0")
    print(f"  前端地址: {url}/")
    print(f"  API文档:  {url}/docs")
    print(f"{'=' * 50}\n")

    if not args.no_browser:
        webbrowser.open(f"{url}/")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
