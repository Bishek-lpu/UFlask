# Response Helpers

Every view function must return a **response**. uFlask accepts several return value styles and provides helper functions that mirror Flask's API.

---

## Return Value Styles

uFlask normalises whatever your function returns into a `Response` object:

```python
# 1. Plain string → 200 text/html
return "Hello, World!"

# 2. Dict or list → 200 application/json (auto-serialised)
return {"status": "ok"}
return [1, 2, 3]

# 3. Tuple (body, status)
return "Created", 201

# 4. Tuple (body, status, content_type)
return "<h1>Hi</h1>", 200, "text/html; charset=utf-8"

# 5. Tuple (body, status, headers_dict)
return "ok", 200, {"X-Custom": "value"}

# 6. None → 204 No Content
return None

# 7. Response object → passed through unchanged
return Response("body", 200)

# 8. FileResponse → streamed file
return FileResponse("/static/data.csv")
```

---

## `jsonify()` — JSON Response

```python
from uflask import jsonify

@app.get("/status")
def status(request):
    return jsonify({"ok": True, "version": "1.0.0"})

# Custom status code
return jsonify({"id": 42}, status=201)

# Extra headers
return jsonify(data, headers={"X-Total-Count": "100"})
```

> `Content-Type` is automatically set to `application/json`.

---

## `redirect()` — HTTP Redirect

```python
from uflask import redirect

# 302 Found (temporary, default)
return redirect("/login")

# 301 Moved Permanently
return redirect("https://new-domain.com", 301)

# 303 See Other (after POST)
return redirect("/dashboard", 303)

# 307 Temporary Redirect (preserves method)
return redirect("/new-endpoint", 307)
```

---

## `make_response()` — Build Manually

```python
from uflask import make_response

@app.post("/login")
def login(request):
    resp = make_response()          # empty 200
    resp.body    = ""
    resp.status  = 302
    resp.headers["Location"] = "/dashboard"
    resp.set_cookie("session", "token-abc", httponly=True)
    return resp

# With initial body and status
resp = make_response("<h1>Hello</h1>", 200, content_type="text/html")
```

---

## `send_file()` — Stream a File

```python
from uflask import send_file

@app.get("/download")
def download(request):
    return send_file("/data/sensor_log.csv")

# Force download with a custom filename
return send_file("/data/log.bin", download_name="export.bin")
```

uFlask reads the MIME type from the file extension and sets `Content-Length` automatically.

| Extension | MIME Type |
|---|---|
| `.html` | `text/html; charset=utf-8` |
| `.json` | `application/json` |
| `.csv` | `text/plain; charset=utf-8` |
| `.png` | `image/png` |
| `.jpg` | `image/jpeg` |
| `.js` | `application/javascript` |
| `.css` | `text/css` |
| `.bin` | `application/octet-stream` |

---

## `abort()` — Raise HTTP Errors

Stop execution immediately and return an error response:

```python
from uflask import abort

@app.get("/admin")
def admin(request):
    if not request.headers.get("x-admin-key"):
        abort(403)                       # Forbidden
    return jsonify({"panel": "open"})

# With a custom message
abort(404, "User not found")
abort(400, "Missing 'email' field")
abort(503, "Database is offline")
```

> `abort()` raises an `HTTPException`. It can be caught by a registered `@app.errorhandler`.

---

## `Response` Object

You can build a `Response` directly for full control:

```python
from uflask import Response

resp = Response(
    body         = "<h1>Hello</h1>",
    status       = 200,
    headers      = {"X-Frame-Options": "DENY"},
    content_type = "text/html; charset=utf-8",
)
```

### Setting headers

```python
resp.headers["Cache-Control"] = "no-cache"
resp.set_header("X-Custom", "value")   # chainable
```

---

## Cookies

### Set a cookie

```python
resp = make_response()
resp.set_cookie(
    key      = "session",
    value    = "token-12345",
    max_age  = 3600,          # seconds until expiry
    path     = "/",           # cookie scope
    domain   = None,          # defaults to current host
    secure   = True,          # HTTPS only
    httponly = True,          # not accessible from JS
    samesite = "Strict",      # "Strict" | "Lax" | "None"
)
return resp
```

### Delete a cookie

```python
resp = make_response()
resp.delete_cookie("session")
resp.status = 302
resp.headers["Location"] = "/login"
return resp
```

### Chaining

```python
return (
    make_response()
    .set_cookie("theme", "dark")
    .set_cookie("lang",  "en")
    .set_header("X-Logged-In", "false")
)
```

---

## `FileResponse` Object

`FileResponse` is a special `Response` that **streams** a file from the filesystem in 512-byte chunks, keeping RAM usage low.

```python
from uflask import FileResponse

@app.get("/export")
def export(request):
    return FileResponse(
        filename      = "/data/export.csv",
        download_name = "data.csv",    # Content-Disposition: attachment
    )
```

If the file does not exist, `FileResponse` automatically returns **404**.

---

## HTTP Status Code Reference

| Code | Meaning | Usage |
|---|---|---|
| 200 | OK | Successful GET / PUT |
| 201 | Created | Successful POST |
| 204 | No Content | DELETE with no body |
| 301 | Moved Permanently | Permanent redirect |
| 302 | Found | Temporary redirect |
| 303 | See Other | Redirect after POST |
| 400 | Bad Request | Missing / invalid input |
| 401 | Unauthorized | Auth required |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Resource missing |
| 405 | Method Not Allowed | Wrong HTTP method |
| 409 | Conflict | Duplicate resource |
| 413 | Payload Too Large | Body exceeds limit |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limited |
| 500 | Internal Server Error | Unexpected crash |
| 503 | Service Unavailable | Maintenance mode |
