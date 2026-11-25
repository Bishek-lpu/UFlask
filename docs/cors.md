# CORS

**Cross-Origin Resource Sharing (CORS)** allows web pages served from one domain to make HTTP requests to your Pico W API from a different domain (e.g., a React app on `localhost:3000` calling `http://pico.local/api`).

---

## Quick Setup

```python
from uflask import UFlask, CORS

app  = UFlask(__name__)
cors = CORS(app)   # allow all origins
```

That's it. Every response will now include the necessary CORS headers.

---

## Configuration

```python
cors = CORS(
    app,
    origins       = "*",                                # who can call this API
    methods       = ["GET", "POST", "PUT", "DELETE"],   # allowed HTTP methods
    allow_headers = ["Content-Type", "Authorization"],  # headers the browser may send
    expose_headers= ["X-Total-Count"],                  # headers the browser may read
    credentials   = False,                              # allow cookies / auth headers
    max_age       = 600,                                # preflight cache (seconds)
)
```

### Parameter Reference

| Parameter | Type | Default | Description |
|---|---|---|---|
| `origins` | `str \| list` | `"*"` | Allowed origins. `"*"` = any. List = whitelist. |
| `methods` | `list` | All methods | HTTP methods the browser may use |
| `allow_headers` | `list` | Common headers | Headers the browser is permitted to send |
| `expose_headers` | `list` | `[]` | Response headers the browser JS can access |
| `credentials` | `bool` | `False` | Allow cookies and `Authorization` headers |
| `max_age` | `int` | `600` | Seconds the browser may cache the preflight result |

---

## Origins

### Allow everyone (open API)

```python
CORS(app, origins="*")
```

### Allow specific origins (production)

```python
CORS(app, origins=[
    "https://myfrontend.com",
    "https://www.myfrontend.com",
    "http://localhost:3000",    # for development
])
```

### Allow with credentials

When `credentials=True`, the browser sends cookies and `Authorization` headers cross-origin. The wildcard `*` cannot be used with credentials — uFlask automatically echoes the specific request origin instead.

```python
CORS(
    app,
    origins     = ["https://myfrontend.com"],
    credentials = True,
)
```

Your frontend must also set:

```javascript
fetch("http://pico.local/api/data", {
    credentials: "include",   // ← send cookies
})
```

---

## Preflight Requests (OPTIONS)

Browsers send an `OPTIONS` preflight request before a cross-origin request with a custom method or headers. uFlask handles this automatically and returns a `204 No Content` response with the correct `Access-Control-*` headers.

You do **not** need to register an `OPTIONS` route for each endpoint.

```
Browser                              Pico W
   |                                    |
   |-- OPTIONS /api/users ------------->|
   |   Origin: https://frontend.com     |
   |   Access-Control-Request-Method: POST
   |                                    |
   |<-- 204 No Content -----------------|
   |   Access-Control-Allow-Origin: https://frontend.com
   |   Access-Control-Allow-Methods: GET, POST, PUT, …
   |   Access-Control-Max-Age: 600
   |                                    |
   |-- POST /api/users ---------------->|
   |   Origin: https://frontend.com     |
   |   Content-Type: application/json   |
   |                                    |
   |<-- 201 Created --------------------|
   |   Access-Control-Allow-Origin: https://frontend.com
```

---

## Expose Headers

By default, browsers can only read "simple" response headers (like `Content-Type`). To allow your JS to read custom headers like `X-Total-Count`, expose them:

```python
CORS(app, expose_headers=["X-Total-Count", "X-Request-ID"])
```

```python
@app.get("/api/users")
def list_users(request):
    users = get_all_users()
    resp  = jsonify(users)
    resp.headers["X-Total-Count"] = str(len(users))
    return resp
```

```javascript
// Now readable in the browser:
const total = response.headers.get("X-Total-Count");
```

---

## Headers Added by CORS

uFlask adds these headers to every response (when the origin is allowed):

| Header | Value |
|---|---|
| `Access-Control-Allow-Origin` | The allowed origin (`*` or the echoed origin) |
| `Access-Control-Allow-Methods` | Comma-separated list of methods |
| `Access-Control-Allow-Headers` | Comma-separated list of headers |
| `Access-Control-Max-Age` | Preflight cache duration |
| `Access-Control-Allow-Credentials` | `"true"` (only when `credentials=True`) |
| `Access-Control-Expose-Headers` | (only when `expose_headers` is set) |
| `Vary` | `Origin` (only when a specific origin is allowed) |

---

## Common Recipes

### React / Vite development

```python
CORS(app, origins=["http://localhost:5173", "http://localhost:3000"])
```

### Mobile app + production frontend

```python
CORS(app, origins=[
    "https://myapp.com",
    "capacitor://localhost",   # Ionic/Capacitor
    "ionic://localhost",
])
```

### Fully open sensor API

```python
CORS(app, origins="*", methods=["GET"])   # read-only
```

### Authenticated API with sessions

```python
CORS(app,
    origins     = ["https://dashboard.myproject.com"],
    credentials = True,
    allow_headers = ["Content-Type", "Authorization", "X-CSRF-Token"],
    max_age     = 3600,
)
```

---

## Disabling CORS on Specific Routes

CORS is applied globally. To skip it for a specific route, return a response from a `before_request` hook before CORS is applied, or manually remove the headers in an `after_request` hook:

```python
@app.after_request
def remove_cors_for_internal(request, response):
    if request.path.startswith("/internal/"):
        response.headers.pop("Access-Control-Allow-Origin", None)
    return response
```
