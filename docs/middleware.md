# Middleware & Hooks

Hooks let you run code **before or after every request** without modifying individual view functions. This is ideal for authentication, logging, response headers, and cleanup.

---

## Overview

uFlask provides four hook types, mirroring Flask:

| Hook | When it runs | Can return a Response? |
|---|---|---|
| `before_first_request` | Once, before the very first request | No |
| `before_request` | Before every route handler | ✅ Yes (short-circuits) |
| `after_request` | After every route handler | Must return response |
| `teardown_request` | Always, even after errors | No |

---

## `@app.before_request`

Runs **before** the route handler. If your function returns a non-`None` value, that value becomes the response and the route handler is **not called**.

```python
@app.before_request
def require_auth(request):
    # Protect all /api/ routes
    if request.path.startswith("/api/"):
        token = request.headers.get("authorization", "")
        if not token.startswith("Bearer "):
            from uflask import jsonify
            return jsonify({"error": "Unauthorized"}), 401
    # Return None to continue normally
```

### Multiple before_request hooks

Hooks run in **registration order**. Returning a response from any hook short-circuits the remaining hooks and the route handler.

```python
@app.before_request
def log_request(request):
    print("→", request.method, request.path)
    # returns None → continues to next hook

@app.before_request
def check_maintenance(request):
    if app.config.get("MAINTENANCE"):
        return jsonify({"error": "Maintenance mode"}), 503
    # returns None → route handler is called
```

---

## `@app.after_request`

Runs **after** the route handler. Receives `(request, response)` and **must return a response** (the same or a new one).

```python
@app.after_request
def add_security_headers(request, response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"]        = "DENY"
    response.headers["X-Powered-By"]           = "uFlask on Pico W"
    return response      # ← must return

@app.after_request
def add_cors_vary(request, response):
    if "origin" in request.headers:
        response.headers.setdefault("Vary", "Origin")
    return response
```

---

## `@app.teardown_request`

Runs **after every request**, regardless of whether an exception occurred. Useful for cleanup (closing DB connections, releasing locks). Return value is **ignored**.

```python
@app.teardown_request
def cleanup(request, exc):
    if exc:
        print("Error during %s %s: %s" % (request.method, request.path, exc))
    # release resources, close files, etc.
```

> `exc` is the exception object if an error occurred, `None` otherwise.

---

## `@app.before_first_request`

Runs **once**, before the very first request is handled. Use it for one-time startup tasks.

```python
import time

@app.before_first_request
def startup():
    app.config["started_at"] = time.time()
    print("🚀 Server started, loading initial data…")
    # initialize sensors, open files, etc.
```

---

## Practical Examples

### Authentication Middleware

```python
# Token-based API auth
_API_TOKENS = {"device-01": "abc123", "device-02": "xyz789"}

@app.before_request
def api_auth(request):
    if not request.path.startswith("/api/"):
        return   # skip non-API routes

    token = request.headers.get("x-api-token", "")
    if token not in _API_TOKENS.values():
        from uflask import jsonify
        return jsonify({"error": "Invalid token"}), 401

    # Store the device name for use in route handlers
    request.view_args["_device"] = [
        k for k, v in _API_TOKENS.items() if v == token
    ][0]
```

### Request Logger

```python
import time

@app.before_request
def start_timer(request):
    request._start = time.ticks_ms()

@app.after_request
def log_response(request, response):
    elapsed = time.ticks_diff(time.ticks_ms(), getattr(request, "_start", 0))
    print("[%s] %s %s → %d (%dms)" % (
        request.remote_addr or "-",
        request.method,
        request.path,
        response.status,
        elapsed,
    ))
    return response
```

### Rate Limiter (Simple)

```python
_request_counts = {}

@app.before_request
def rate_limit(request):
    ip = request.remote_addr or "unknown"
    _request_counts[ip] = _request_counts.get(ip, 0) + 1
    if _request_counts[ip] > 100:
        from uflask import jsonify
        return jsonify({"error": "Too many requests"}), 429
```

### JSON-only Enforcement

```python
@app.before_request
def require_json_on_post(request):
    if request.method in ("POST", "PUT", "PATCH"):
        if request.content_length > 0 and not request.is_json:
            from uflask import jsonify
            return jsonify({"error": "Content-Type must be application/json"}), 415
```

### Add Response Headers Globally

```python
@app.after_request
def global_headers(request, response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Server"]        = "uFlask/1.0.0"
    return response
```

### Session Validation

```python
# Public paths that don't need a session
_PUBLIC = {"/login", "/logout", "/health", "/static"}

@app.before_request
def session_guard(request):
    for pub in _PUBLIC:
        if request.path.startswith(pub):
            return   # skip auth for public routes

    session = request.cookies.get("session")
    if not session:
        from uflask import redirect
        return redirect("/login")
```

---

## Hook Execution Order

```
Incoming request
       │
       ▼
before_first_request  (once only)
       │
       ▼
before_request hooks  (in order; first non-None response short-circuits)
       │
       ▼
   Route handler
       │
       ▼
after_request hooks   (in order; must return response)
       │
       ▼
  CORS headers applied
       │
       ▼
  Response sent to client
       │
       ▼
teardown_request hooks (always; exc is None or the error)
```

---

## MiddlewareStack API

You can also register hooks programmatically (without decorators):

```python
def my_hook(request):
    print("before:", request.path)

app.middleware.add_before(my_hook)
app.middleware.add_after(lambda req, resp: resp)
app.middleware.add_teardown(lambda req, exc: None)
app.middleware.add_before_first(lambda: None)
```
