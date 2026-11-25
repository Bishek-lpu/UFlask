# Request Object

The `request` object is passed as the **first argument** to every view function. It exposes everything about the incoming HTTP request.

---

## Attribute Reference

| Attribute | Type | Description |
|---|---|---|
| `request.method` | `str` | HTTP method: `"GET"`, `"POST"`, `"PUT"` … |
| `request.path` | `str` | URL path: `"/api/users"` |
| `request.full_path` | `str` | Path + query string: `"/api/users?page=2"` |
| `request.url` | `str` | Full URL: `"http://pico.local/api/users?page=2"` |
| `request.base_url` | `str` | URL without query string |
| `request.host` | `str` | `Host` header value: `"pico.local"` |
| `request.protocol` | `str` | `"HTTP/1.1"` |
| `request.args` | `MultiDict` | Parsed query-string parameters |
| `request.form` | `MultiDict` | URL-encoded or multipart form fields |
| `request.files` | `dict` | Uploaded files (multipart only) |
| `request.json` | `any` | Parsed JSON body (or `None`) |
| `request.data` | `bytes` | Raw request body |
| `request.headers` | `dict` | Lower-cased header names |
| `request.cookies` | `dict` | Parsed `Cookie` header |
| `request.remote_addr` | `str\|None` | Client IP address |
| `request.content_type` | `str` | `Content-Type` header |
| `request.content_length` | `int` | Body length in bytes |
| `request.is_json` | `bool` | `True` when Content-Type is `application/json` |
| `request.is_secure` | `bool` | `True` when `X-Forwarded-Proto: https` |
| `request.user_agent` | `str` | `User-Agent` header |
| `request.referrer` | `str\|None` | `Referer` header |
| `request.authorization` | `str\|None` | Raw `Authorization` header |
| `request.endpoint` | `str\|None` | Matched function name |
| `request.view_args` | `dict` | URL path parameters |

---

## Query String Parameters — `request.args`

```python
# GET /search?q=temperature&limit=5&page=2

@app.get("/search")
def search(request):
    q     = request.args.get("q", "")          # "temperature"
    limit = int(request.args.get("limit", 10)) # 5
    page  = int(request.args.get("page",  1))  # 2
    return jsonify({"q": q, "limit": limit, "page": page})
```

### Multiple values for the same key

```python
# GET /filter?tag=python&tag=web&tag=pico

tags = request.args.getlist("tag")
# → ["python", "web", "pico"]
```

### Check if a parameter exists

```python
if "debug" in request.args:
    # ?debug was present in the URL
    pass
```

---

## Form Data — `request.form`

Populated from `application/x-www-form-urlencoded` and `multipart/form-data` bodies.

```python
# POST /register  with  Content-Type: application/x-www-form-urlencoded
# Body: username=alice&email=alice%40example.com&role=admin

@app.post("/register")
def register(request):
    username = request.form.get("username", "")
    email    = request.form.get("email",    "")
    role     = request.form.get("role",     "user")
    return jsonify({"username": username, "email": email, "role": role})
```

### Multiple values

```python
# Body: color=red&color=blue

colors = request.form.getlist("color")
# → ["red", "blue"]
```

---

## JSON Body — `request.json` / `get_json()`

```python
# POST /api/users
# Content-Type: application/json
# Body: {"name": "Alice", "age": 30}

@app.post("/api/users")
def create_user(request):
    # Quick access (populated automatically)
    data = request.json         # dict or None

    # Safe access with options
    data = request.get_json(
        force  = False,   # True → parse even without JSON Content-Type
        silent = True,    # True → return None on parse error (default)
    )

    if not data:
        return jsonify({"error": "JSON body required"}), 400

    name = data.get("name", "").strip()
    age  = int(data.get("age", 0))
    return jsonify({"name": name, "age": age}), 201
```

> **Tip:** `request.json` is `None` when the body is missing, empty, or not valid JSON (unless `silent=False`).

---

## Raw Body — `request.data` / `get_data()`

```python
@app.post("/raw")
def raw(request):
    # As bytes (default)
    raw_bytes = request.data

    # As a string
    raw_text = request.get_data(as_text=True)

    return jsonify({"length": len(raw_bytes)})
```

---

## Headers — `request.headers`

All header names are stored in **lowercase**.

```python
# Request had:  Authorization: Bearer my-token
#               X-Request-ID: abc-123

auth     = request.headers.get("authorization")     # "Bearer my-token"
req_id   = request.headers.get("x-request-id", "")  # "abc-123"
ua       = request.headers.get("user-agent", "")
host     = request.headers.get("host", "")
```

Shortcut properties:

```python
request.user_agent     # → "Mozilla/5.0 …"
request.authorization  # → "Bearer my-token"
request.referrer       # → "https://example.com/"
request.host           # → "pico.local"
```

---

## Cookies — `request.cookies`

```python
# Request had: Cookie: session=abc123; theme=dark

session = request.cookies.get("session")  # "abc123"
theme   = request.cookies.get("theme", "light")  # "dark"

# Check if a cookie exists
if "session" not in request.cookies:
    return redirect("/login")
```

---

## File Uploads — `request.files`

For `multipart/form-data` forms with file inputs:

```html
<form method="POST" enctype="multipart/form-data" action="/upload">
  <input type="file" name="photo">
  <button>Upload</button>
</form>
```

```python
@app.post("/upload")
def upload(request):
    file = request.files.get("photo")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    # file is a dict:
    # {
    #   "filename":     "photo.jpg",
    #   "content_type": "image/jpeg",
    #   "data":         b"<raw bytes>",
    # }

    # Save it
    with open("/uploads/" + file["filename"], "wb") as f:
        f.write(file["data"])

    return jsonify({
        "saved":    file["filename"],
        "size":     len(file["data"]),
        "type":     file["content_type"],
    }), 201
```

> **Note:** The Pico W has 2 MB of flash. Keep uploaded files small. `max_body_size` (default 8 kB) limits the total request body size.

---

## Combined Values — `request.values()`

Returns a merged dict of `args` and `form`, with query-string values taking priority:

```python
# Works whether the value came from ?id=5 or the form body
item_id = request.values().get("id")
```

---

## Remote Address

```python
client_ip = request.remote_addr   # "192.168.1.42" or None
```

---

## MultiDict API

Both `request.args` and `request.form` are `MultiDict` instances.

```python
md = request.args

md.get("key")                # last value (or None)
md.get("key", "default")     # last value with default
md.getlist("key")            # all values as list
md["key"]                    # last value (KeyError if missing)
"key" in md                  # membership test
md.to_dict()                 # plain dict (last value per key)
```
