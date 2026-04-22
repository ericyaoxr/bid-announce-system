import urllib.request
import json

BASE = "http://localhost:8000"

def test(name, url, method="GET", data=None):
    try:
        if data:
            req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
        else:
            req = urllib.request.Request(url)
        r = urllib.request.urlopen(req)
        body = r.read().decode()
        print(f"OK   {name}: {r.status}")
        return r.status, body, r.headers
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"FAIL {name}: {e.code} {e.reason}")
        return e.code, body, e.headers

# 1. Health
test("Health", f"{BASE}/api/health")

# 2. Root page
status, body, _ = test("Root page", f"{BASE}/")
has_root = 'id="root"' in body
print(f"     Has root div: {has_root}")

# 3. Assets JS
test("Assets JS", f"{BASE}/assets/index-D8zXtGlX.js")

# 4. Assets CSS
test("Assets CSS", f"{BASE}/assets/index-BbR7p8Tp.css")

# 5. SPA routing
status, body, _ = test("SPA /announcements", f"{BASE}/announcements")
has_root = 'id="root"' in body
print(f"     Has root div: {has_root}")

# 6. SPA routing /login
status, body, _ = test("SPA /login", f"{BASE}/login")
has_root = 'id="root"' in body
print(f"     Has root div: {has_root}")

# 7. Login API
status, body, _ = test("Login API", f"{BASE}/api/auth/login", data={"username": "admin", "password": "admin"})
if status == 200:
    data = json.loads(body)
    print(f"     Has token: {'access_token' in data}")
    print(f"     Username: {data.get('username')}")
    print(f"     Is admin: {data.get('is_admin')}")

# 8. Dashboard API (needs auth)
status, body, _ = test("Login for token", f"{BASE}/api/auth/login", data={"username": "admin", "password": "admin"})
if status == 200:
    token = json.loads(body)["access_token"]
    req = urllib.request.Request(f"{BASE}/api/dashboard")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        r = urllib.request.urlopen(req)
        print(f"OK   Dashboard API: {r.status}")
    except urllib.error.HTTPError as e:
        print(f"FAIL Dashboard API: {e.code} {e.reason}")

# 9. Announcements API
status, body, _ = test("Announcements API", f"{BASE}/api/announcements?page=1&size=5")
if status == 200:
    data = json.loads(body)
    print(f"     Total: {data.get('total')}, Items: {len(data.get('items', []))}")

# 10. Docs
test("API Docs", f"{BASE}/docs")

print("\n=== All tests completed ===")
