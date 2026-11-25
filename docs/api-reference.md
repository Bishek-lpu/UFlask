# API Reference

Complete reference for every public symbol exported by uFlask.

---

## `UFlask`

The main application class.

```python
from uflask import UFlask

app = UFlask(
    name          = __name__,     # str  – application name
    host          = "0.0.0.0",   # str  – bind address
    port          = 80,           # int  – TCP port
    debug         = False,        # bool – enable debug mode
    static_dir    = "static",     # str  – filesystem directory for static files
    static_url    = "/static",    # str  – URL prefix for static files
    max_body_size = 8192,         # int  – max request body in bytes
    backlog       = 5,            # int  – TCP listen backlog
)
```

### Route decorators

| Method | Description |
|---|---|
| `@app.get(path)` | Register a `GET` route |
| `@app.post(path)` | Register a `POST` route |
| `@app.put(path)` | Register a `PUT` route |
| `@app.patch(path)` | Register a `PATCH` route |
| `@app.delete(path)` | Register a `DELETE` route |
| `@app.options(path)` | Register an `OPTIONS` route |
| `@app.head(path)` | Register a `HEAD` route |
| `@app.route(path, methods=[…])` | Register with explicit method list |

### Hook decorators

| Method | Description |
|---|---|
| `@app.before_request` | Run before every route handler |
| `@app.after_request` | Run after every route handler (must return response) |
| `@app.teardown_request` | Run after every request (even on error) |
| `@app.before_first_request` | Run once before the first request |
| `@app.errorhandler(code_or_exc)` | Register a custom error handler |

### Methods

| Method | Description |
|---|---|
| `app.register_blueprint(bp)` | Attach a Blueprint to this app |
| `app.url_for(endpoint, **values)` | Reverse URL building |
| `app.run(host, port, debug)` | Start the server (blocking) |

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `app.name` | `str` | Application name |
| `app.debug` | `bool` | Debug mode flag |
| `app.cors` | `CORS \| None` | Attached CORS instance |
| `app.config` | `dict` | Arbitrary key/value config store |
| `app.VERSION` | `str` | uFlask version string |

---

## `Request`

Passed as the first argument to every view function.

| Attribute | Type | Description |
|---|---|---|
| `.method` | `str` | `"GET"`, `"POST"`, etc. |
| `.path` | `str` | URL path |
| `.full_path` | `str` | Path + query string |
| `.url` | `str` | Full URL |
| `.base_url` | `str` | URL without query |
| `.host` | `str` | Host header |
| `.protocol` | `str` | `"HTTP/1.1"` |
| `.args` | `MultiDict` | Query parameters |
| `.form` | `MultiDict` | Form fields |
| `.files` | `dict` | Uploaded files |
| `.json` | `any` | Parsed JSON body |
| `.data` | `bytes` | Raw body |
| `.headers` | `dict` | Lower-cased headers |
| `.cookies` | `dict` | Parsed cookies |
| `.remote_addr` | `str\|None` | Client IP |
| `.content_type` | `str` | Content-Type header |
| `.content_length` | `int` | Body size |
| `.is_json` | `bool` | JSON content type? |
| `.is_secure` | `bool` | HTTPS? |
| `.user_agent` | `str` | User-Agent header |
| `.referrer` | `str\|None` | Referer header |
| `.authorization` | `str\|None` | Authorization header |
| `.endpoint` | `str\|None` | Matched function name |
| `.view_args` | `dict` | URL parameters |

| Method | Returns | Description |
|---|---|---|
| `.get_json(force, silent)` | `any` | Parse JSON body |
| `.get_data(as_text)` | `bytes\|str` | Get raw body |
| `.values()` | `dict` | Merged args + form |

---

## `MultiDict`

```python
md.get(key, default=None)      # → last value or default
md.getlist(key, default=[])    # → all values as list
md[key]                        # → last value (KeyError if missing)
key in md                      # → bool
md.to_dict()                   # → plain dict
md.add(key, value)             # add a value
```

---

## `Response`

```python
Response(
    body         = "",                      # str | bytes | None
    status       = 200,                     # int
    headers      = None,                    # dict | None
    content_type = "text/html; charset=utf-8",
)
```

| Method | Returns | Description |
|---|---|---|
| `.set_cookie(key, value, max_age, path, domain, secure, httponly, samesite)` | `self` | Set a cookie |
| `.delete_cookie(key, path, domain)` | `self` | Expire a cookie |
| `.set_header(key, value)` | `self` | Set a header |
| `.status_line` | `str` | `"200 OK"` |

---

## `FileResponse`

```python
FileResponse(
    filename      = "/path/to/file",   # str
    status        = 200,               # int
    headers       = None,              # dict | None
    download_name = None,              # str | None — sets Content-Disposition
)
```

Automatically detects MIME type from extension and sets `Content-Length`. Returns 404 if the file does not exist.

---

## Helper Functions

### `jsonify(data, status=200, headers=None)`

```python
jsonify({"key": "value"})
jsonify(data, status=201)
jsonify(data, headers={"X-Count": "5"})
```

Returns a `Response` with `Content-Type: application/json`.

### `redirect(location, status=302)`

```python
redirect("/login")
redirect("https://example.com", 301)
```

### `make_response(body="", status=200, headers=None, content_type=None)`

```python
resp = make_response("<html>…</html>", 200, content_type="text/html")
resp.set_cookie("session", "token")
return resp
```

### `send_file(filename, headers=None, download_name=None)`

```python
send_file("/data/export.csv")
send_file("/data/log.bin", download_name="log.bin")
```

### `abort(status, description=None)`

```python
abort(404)
abort(400, "Invalid input")
```

Raises `HTTPException` immediately.

### `render_template(filename, **context)`

```python
html = render_template("index.html", title="Home", items=[…])
```

### `render_string(source, **context)`

```python
html = render_string("Hello {{ name }}!", name="Alice")
```

### `set_templates_dir(path)`

```python
set_templates_dir("/flash/templates")
```

---

## `CORS`

```python
CORS(
    app,
    origins       = "*",
    methods       = ["GET","POST","PUT","PATCH","DELETE","OPTIONS","HEAD"],
    allow_headers = ["Content-Type","Authorization"],
    expose_headers= [],
    credentials   = False,
    max_age       = 600,
)
```

---

## `Blueprint`

```python
bp = Blueprint(
    name       = "mymodule",    # str – unique name
    url_prefix = "/api",        # str – path prefix
)
```

Same route decorators as `UFlask`: `.get()`, `.post()`, `.put()`, `.patch()`, `.delete()`, `.route()`.

Same hook decorators: `.before_request`, `.after_request`, `.teardown_request`.

```python
app.register_blueprint(bp)
```

---

## Exceptions

| Class | Code | Constructor |
|---|---|---|
| `HTTPException` | any | `HTTPException(status, description)` |
| `BadRequest` | 400 | `BadRequest(description=None)` |
| `Unauthorized` | 401 | `Unauthorized(description=None)` |
| `Forbidden` | 403 | `Forbidden(description=None)` |
| `NotFound` | 404 | `NotFound(description=None)` |
| `MethodNotAllowed` | 405 | `MethodNotAllowed(allowed_methods, description)` |
| `Conflict` | 409 | `Conflict(description=None)` |
| `Gone` | 410 | `Gone(description=None)` |
| `PayloadTooLarge` | 413 | `PayloadTooLarge(description=None)` |
| `UnsupportedMediaType` | 415 | `UnsupportedMediaType(description=None)` |
| `UnprocessableEntity` | 422 | `UnprocessableEntity(description=None)` |
| `TooManyRequests` | 429 | `TooManyRequests(description, retry_after)` |
| `InternalServerError` | 500 | `InternalServerError(description=None)` |
| `ServiceUnavailable` | 503 | `ServiceUnavailable(description, retry_after)` |

---

## Logging

```python
from uflask import logging, getLogger

# Global logger
logging.set_level(logging.DEBUG)
logging.set_log_file("/log.txt")
logging.enable_color(True)
logging.debug(…)
logging.info(…)
logging.warning(…)
logging.error(…)
logging.critical(…)
logging.exception(msg, exc)

# Named logger
log = getLogger("mymodule")
log.set_level(logging.WARNING)
log.debug(…); log.info(…); log.error(…); log.exception(msg, exc)

# Level constants
logging.DEBUG    # 10
logging.INFO     # 20
logging.WARNING  # 30
logging.ERROR    # 40
logging.CRITICAL # 50
```

---

## Package Info

```python
import uflask

uflask.__version__   # "1.0.0"
```
