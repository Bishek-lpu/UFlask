# Blueprints

Blueprints let you **split a large application into small, focused modules**. Each Blueprint is a mini-app with its own routes and hooks; you then register it on the main `UFlask` app.

---

## Why Use Blueprints?

Without Blueprints, every route lives in `main.py`. As your app grows, that file becomes hard to manage:

```
main.py           ← 500 lines of routes for users, sensors, auth, admin…
```

With Blueprints, each domain gets its own file:

```
main.py           ← app setup + blueprint registration
auth.py           ← @auth.get("/login") @auth.post("/login")
sensors.py        ← @sensors.get("/temperature")
users.py          ← @users.get("/") @users.post("/")
```

---

## Creating a Blueprint

```python
# sensors.py
from uflask import Blueprint, jsonify

# name       → unique identifier (used in url_for and log messages)
# url_prefix → prepended to every route in this blueprint
sensors = Blueprint("sensors", url_prefix="/api/sensors")

@sensors.get("/temperature")
def temperature(request):
    return jsonify({"celsius": 24.5})

@sensors.get("/humidity")
def humidity(request):
    return jsonify({"percent": 61.0})

@sensors.post("/reading")
def post_reading(request):
    data = request.get_json()
    return jsonify({"saved": True, "data": data}), 201
```

---

## Registering on the App

```python
# main.py
from uflask import UFlask
from sensors import sensors

app = UFlask(__name__)
app.register_blueprint(sensors)

app.run()
```

After registration:

| Blueprint route | Final URL |
|---|---|
| `GET /temperature` | `GET /api/sensors/temperature` |
| `GET /humidity` | `GET /api/sensors/humidity` |
| `POST /reading` | `POST /api/sensors/reading` |

---

## Blueprint Hooks

Blueprints support their own `before_request`, `after_request`, and `teardown_request` hooks. These are **registered globally** on the app when the blueprint is registered (they apply to all routes, not only the blueprint's).

```python
sensors = Blueprint("sensors", url_prefix="/api/sensors")

@sensors.before_request
def require_api_key(request):
    """Runs before every request (globally after registration)."""
    if request.path.startswith("/api/sensors"):
        key = request.headers.get("x-api-key")
        if key != "my-secret":
            from uflask import abort
            abort(401, "Invalid API key")

@sensors.after_request
def add_cache_header(request, response):
    response.headers["Cache-Control"] = "no-cache"
    return response

@sensors.teardown_request
def log_sensor_request(request, exc):
    if exc:
        print("Sensor error:", exc)
```

> **Tip:** To scope hooks to only a blueprint's routes, check `request.path` or `request.endpoint` inside the hook.

---

## Route Decorators Available on Blueprint

```python
bp = Blueprint("api", url_prefix="/api")

@bp.get("/items")          # GET
@bp.post("/items")         # POST
@bp.put("/items/<int:id>") # PUT
@bp.patch("/items/<id>")   # PATCH
@bp.delete("/items/<id>")  # DELETE
@bp.route("/data", methods=["GET","POST"])  # multiple
```

---

## Multiple Blueprints

```python
# main.py
from uflask import UFlask, CORS
from auth    import auth_bp
from api     import api_bp
from sensors import sensor_bp

app = UFlask(__name__, debug=True)
CORS(app, origins="*")

app.register_blueprint(auth_bp)     # /auth/…
app.register_blueprint(api_bp)      # /api/…
app.register_blueprint(sensor_bp)   # /sensors/…

app.run()
```

---

## Full Example — Auth Blueprint

```python
# auth.py
from uflask import Blueprint, jsonify, redirect, make_response, abort

auth_bp = Blueprint("auth", url_prefix="/auth")

_USERS = {"admin": "pico123", "user1": "secret"}

@auth_bp.get("/login")
def login_page(request):
    from uflask import render_template
    return render_template("login.html", error="")

@auth_bp.post("/login")
def login(request):
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    if _USERS.get(username) == password:
        resp = make_response()
        resp.set_cookie("session", username, httponly=True, max_age=3600)
        resp.status = 302
        resp.headers["Location"] = "/dashboard"
        return resp
    from uflask import render_template
    return render_template("login.html", error="Invalid credentials"), 401

@auth_bp.get("/logout")
def logout(request):
    resp = make_response()
    resp.delete_cookie("session")
    resp.status = 302
    resp.headers["Location"] = "/auth/login"
    return resp

@auth_bp.before_request
def check_session(request):
    """Protect /auth/logout — must be logged in."""
    if request.path == "/auth/logout":
        if "session" not in request.cookies:
            return redirect("/auth/login")
```

---

## `url_for()` with Blueprints

```python
# endpoint name = "blueprint_name.function_name"
url = app.url_for("sensors.temperature")
# → "/api/sensors/temperature"

url2 = app.url_for("auth.login_page")
# → "/auth/login"
```

---

## Blueprint Reference

| Attribute / Method | Description |
|---|---|
| `Blueprint(name, url_prefix)` | Create a blueprint |
| `@bp.get(path)` | Register a GET route |
| `@bp.post(path)` | Register a POST route |
| `@bp.put(path)` | Register a PUT route |
| `@bp.patch(path)` | Register a PATCH route |
| `@bp.delete(path)` | Register a DELETE route |
| `@bp.route(path, methods=[…])` | Register with explicit methods |
| `@bp.before_request` | Register a before-request hook |
| `@bp.after_request` | Register an after-request hook |
| `@bp.teardown_request` | Register a teardown hook |
| `app.register_blueprint(bp)` | Attach blueprint to the app |
| `bp.name` | Blueprint name |
| `bp.url_prefix` | URL prefix |
