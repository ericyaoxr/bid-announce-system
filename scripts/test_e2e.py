import urllib.request
import json

BASE = "http://localhost:8000"

def get(url, headers=None):
    req = urllib.request.Request(url)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        r = urllib.request.urlopen(req)
        return r.status, json.loads(r.read()) if r.headers.get('Content-Type', '').startswith('application/json') else r.read().decode(), r.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode() if e.fp else "", e.headers

def post(url, data=None, headers=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", **(headers or {})}, method='POST')
    try:
        r = urllib.request.urlopen(req)
        return r.status, json.loads(r.read()) if r.headers.get('Content-Type', '').startswith('application/json') else r.read().decode(), r.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode() if e.fp else "", e.headers

print("=" * 60)
print("  端到端全面自测")
print("=" * 60)

# 1. 登录获取 token
print("\n[1] 认证流程")
status, data, _ = post(f"{BASE}/api/auth/login", {"username": "admin", "password": "admin"})
if status == 200:
    token = data["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    print(f"  ✓ 登录成功, token: {token[:20]}...")
else:
    print(f"  ✗ 登录失败: {status}")
    exit(1)

# 2. 获取当前用户
print("\n[2] 用户信息")
status, data, _ = get(f"{BASE}/api/auth/me", auth_headers)
print(f"  {'✓' if status == 200 else '✗'} 用户信息: {data}")

# 3. 仪表盘 API
print("\n[3] 仪表盘 API (/api/dashboard)")
status, data, _ = get(f"{BASE}/api/dashboard", auth_headers)
if status == 200:
    print(f"  ✓ 总公告数: {data.get('total')}")
    print(f"  ✓ 今日新增: {data.get('today')}")
    print(f"  ✓ 中标总金额: {data.get('total_bid_amount')}")
    print(f"  ✓ 分类分布: {len(data.get('by_category', []))} 项")
    print(f"  ✓ 每日趋势: {len(data.get('daily_trend', []))} 项")
    print(f"  ✓ TOP公司: {len(data.get('top_count_companies', []))} 项")
else:
    print(f"  ✗ 失败: {status} {data}")

# 4. 公告列表 API
print("\n[4] 公告列表 API (/api/announcements)")
status, data, _ = get(f"{BASE}/api/announcements?page=1&size=5", auth_headers)
if status == 200:
    print(f"  ✓ 总数: {data.get('total')}, 当前页: {data.get('page')}, 每页: {data.get('size')}")
    print(f"  ✓ 返回项数: {len(data.get('items', []))}")
    if data.get('items'):
        item = data['items'][0]
        print(f"  ✓ 示例标题: {item.get('title', '')[:50]}...")
else:
    print(f"  ✗ 失败: {status} {data}")

# 5. 公告搜索 API
print("\n[5] 公告搜索 API")
import urllib.parse
keyword = urllib.parse.quote("工程")
status, data, _ = get(f"{BASE}/api/announcements?keyword={keyword}&page=1&size=3", auth_headers)
if status == 200:
    print(f"  ✓ 搜索结果: {data.get('total')} 条")
else:
    print(f"  ✗ 失败: {status} {data}")

# 6. 公告详情 API
print("\n[6] 公告详情 API")
status, data, _ = get(f"{BASE}/api/announcements?page=1&size=1", auth_headers)
if status == 200 and data.get('items'):
    ann_id = data['items'][0]['id']
    status2, data2, _ = get(f"{BASE}/api/announcements/{ann_id}", auth_headers)
    if status2 == 200:
        print(f"  ✓ 详情标题: {data2.get('title', '')[:50]}...")
        print(f"  ✓ 中标人: {data2.get('winning_bidders')}")
    else:
        print(f"  ✗ 详情失败: {status2}")
else:
    print(f"  ⊘ 跳过（无公告数据）")

# 7. 采集状态 API
print("\n[7] 采集管理 API (/api/crawler/status)")
status, data, _ = get(f"{BASE}/api/crawler/status", auth_headers)
if status == 200:
    print(f"  ✓ 运行状态: {'运行中' if data.get('is_running') else '空闲'}")
    print(f"  ✓ 当前模式: {data.get('mode')}")
    print(f"  ✓ 日志数: {data.get('log_count')}")
else:
    print(f"  ✗ 失败: {status} {data}")

# 8. 导出 API
print("\n[8] 数据导出 API (/api/export)")
status, data, _ = get(f"{BASE}/api/export/formats", auth_headers)
if status == 200:
    print(f"  ✓ 支持格式: {data}")
else:
    print(f"  ✗ 失败: {status} {data}")

# 9. 定时调度 API
print("\n[9] 定时调度 API (/api/schedules)")
status, data, _ = get(f"{BASE}/api/schedules", auth_headers)
if status == 200:
    print(f"  ✓ 调度任务数: {len(data) if isinstance(data, list) else 'N/A'}")
else:
    print(f"  ✗ 失败: {status} {data}")

# 10. 前端页面渲染
print("\n[10] 前端页面渲染")
pages = ["/", "/login", "/announcements", "/winners", "/crawler", "/export", "/schedules"]
for page in pages:
    status, body, _ = get(f"{BASE}{page}")
    has_root = 'id="root"' in body if isinstance(body, str) else False
    print(f"  {'✓' if status == 200 and has_root else '✗'} {page}: {status} {'有 root div' if has_root else '无 root div'}")

# 11. 静态资源
print("\n[11] 静态资源")
status, _, headers = get(f"{BASE}/assets/index-D8zXtGlX.js")
print(f"  {'✓' if status == 200 else '✗'} JS 文件: {status} {headers.get('Content-Type', '')[:30]}")

status, _, headers = get(f"{BASE}/assets/index-BbR7p8Tp.css")
print(f"  {'✓' if status == 200 else '✗'} CSS 文件: {status} {headers.get('Content-Type', '')[:30]}")

status, _, headers = get(f"{BASE}/favicon.svg")
print(f"  {'✓' if status == 200 else '✗'} Favicon: {status} {headers.get('Content-Type', '')[:30]}")

# 12. 未授权访问测试
print("\n[12] 未授权访问测试")
status, _, _ = get(f"{BASE}/api/crawler/status")
print(f"  {'✓' if status == 200 else '✗'} 采集状态(公开): {status} (公开接口应返回 200)")

status, _, _ = post(f"{BASE}/api/crawler/start", {})
print(f"  {'✓' if status in (401, 403) else '✗'} 采集启动(需认证): {status} (期望 401/403)")

# 13. API 文档
print("\n[13] API 文档")
status, _, _ = get(f"{BASE}/docs")
print(f"  {'✓' if status == 200 else '✗'} Swagger UI: {status}")

status, _, _ = get(f"{BASE}/openapi.json")
print(f"  {'✓' if status == 200 else '✗'} OpenAPI JSON: {status}")

print("\n" + "=" * 60)
print("  测试完成!")
print("=" * 60)
