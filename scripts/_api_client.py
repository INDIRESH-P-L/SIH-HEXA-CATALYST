import json, time, urllib.request, urllib.error
BASE = "http://127.0.0.1:8000"

def call(method, path, body=None, token=None, timeout=180):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")

def wait():
    for _ in range(90):
        try:
            s, _b = call("GET", "/health", timeout=10)
            if s == 200:
                return True
        except Exception:
            time.sleep(1)
    return False

def login(email="priya.sharma@mospi.gov.in", pw="Demo@2026"):
    s, b = call("POST", "/api/v1/auth/login", {"email": email, "password": pw})
    assert s == 200, (s, b)
    return b["access_token"], b["user"]
