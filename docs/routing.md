# Routing

Routing maps an incoming URL to a Python function (a **view function**). uFlask uses decorator-based routing, identical to Flask.

---

## Basic Routes

```python
from uflask import UFlask

app = UFlask(__name__)

@app.route("/")
def index(request):
    return "Welcome to uFlask!"
```

Every view function receives a `request` object as its **first argument**.

---

## HTTP Method Shortcuts

uFlask provides one decorator per HTTP method:

```python
@app.get("/items")        # GET
@app.post("/items")       # POST
@app.put("/items/<id>")   # PUT
@app.patch("/items/<id>") # PATCH
@app.delete("/items/<id>")# DELETE
@app.options("/items")    # OPTIONS
@app.head("/items")       # HEAD
```

### Accept multiple methods on one route

```python
@app.route("/login", methods=["GET", "POST"])
def login(request):
    if request.method == "GET":
        return render_template("login.html")
    # POST — process form
    username = request.form.get("username")
    ...
```

---

## URL Parameters (Converters)

Dynamic segments are wrapped in `< >`. uFlask automatically converts the captured value to the right type.

### String (default)

```python
@app.get("/users/<username>")
def profile(request, username):
    return "Profile: " + username
```

| URL | `username` |
|---|---|
| `/users/alice` | `"alice"` |
| `/users/bob123` | `"bob123"` |

### Integer — `<int:name>`

```python
@app.get("/products/<int:pid>")
def product(request, pid):
    # pid is already an int — no int() needed
    return jsonify({"id": pid})
```

| URL | `pid` | Rejects |
|---|---|---|
| `/products/42` | `42` | |
| `/products/abc` | | ✗ → 404 |

### Float — `<float:name>`

```python
@app.get("/celsius/<float:temp>")
def convert(request, temp):
    return jsonify({"fahrenheit": temp * 9/5 + 32})
```

### Path — `<path:name>` (captures slashes)

```python
@app.get("/files/<path:filename>")
def serve_file(request, filename):
    # filename can contain slashes
    return send_file("/static/" + filename)
```

| URL | `filename` |
|---|---|
| `/files/css/main.css` | `"css/main.css"` |
| `/files/img/logo.png` | `"img/logo.png"` |

---

## Multiple URL Parameters

```python
@app.get("/orgs/<org>/repos/<repo>/issues/<int:issue_id>")
def get_issue(request, org, repo, issue_id):
    return jsonify({
        "org":      org,
        "repo":     repo,
        "issue_id": issue_id,
    })
```

URL: `/orgs/acme/repos/widget/issues/42`

---

## Static Files

uFlask automatically registers a `/static/<path:filename>` route that serves files from the `static/` directory (configurable).

```python
# default: serves from ./static/
app = UFlask(__name__, static_dir="static", static_url="/static")

# custom paths
app = UFlask(__name__, static_dir="www", static_url="/assets")
```

Place files in `static/` and access them at:

```
http://<pico-ip>/static/style.css
http://<pico-ip>/static/app.js
http://<pico-ip>/static/favicon.ico
```

---

## Reverse URL Building — `url_for()`

Build a URL from an endpoint name instead of hardcoding strings:

```python
@app.get("/users/<int:uid>")
def user_detail(request, uid):
    return jsonify({"id": uid})

# Somewhere else:
url = app.url_for("user_detail", uid=5)
# → "/users/5"

# Extra keyword arguments become query parameters
url2 = app.url_for("user_detail", uid=5, include_email=True)
# → "/users/5?include_email=True"
```

---

## Checking the Method Inside a Route

```python
@app.route("/form", methods=["GET", "POST"])
def form(request):
    if request.method == "POST":
        name = request.form.get("name", "")
        return jsonify({"submitted": name})
    # GET — show the form
    return render_template("form.html")
```

---

## Route Registration Order

Routes are matched in **registration order** (first registered, first matched). Put more specific routes before general ones:

```python
# ✅ Specific route first
@app.get("/users/me")
def current_user(request):
    return jsonify({"id": "me"})

# Then the general pattern
@app.get("/users/<uid>")
def get_user(request, uid):
    return jsonify({"id": uid})
```

---

## 405 Method Not Allowed

If a URL matches a route but the HTTP method does not, uFlask automatically returns `405 Method Not Allowed` with an `Allow` header listing the permitted methods.

```python
@app.get("/items")
def list_items(request):
    return jsonify([])

# DELETE /items → 405  {"error": "Method Not Allowed. Allowed: GET"}
```

---

## Blueprints — Splitting Routes Across Files

For larger apps, use [Blueprints](blueprints.md) to register routes from separate modules:

```python
# sensors.py
from uflask import Blueprint, jsonify

bp = Blueprint("sensors", url_prefix="/api/sensors")

@bp.get("/temperature")
def temperature(request):
    return jsonify({"celsius": 24.5})

# main.py
app.register_blueprint(bp)
# → registers GET /api/sensors/temperature
```
