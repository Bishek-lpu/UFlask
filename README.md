# uFlask

> **A Flask-compatible micro web framework for MicroPython / Raspberry Pi Pico W**

[![PyPI](https://img.shields.io/pypi/v/uflask)](https://pypi.org/project/uflask/)
[![Python](https://img.shields.io/pypi/pyversions/uflask)](https://pypi.org/project/uflask/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![MicroPython](https://img.shields.io/badge/MicroPython-1.22%2B-blue)](https://micropython.org)

uFlask brings the **Flask developer experience** to the **Raspberry Pi Pico W** — routing decorators, request/response objects, Jinja2 templates, CORS, Blueprints, middleware hooks, and structured logging, all in pure Python that runs on 264 kB of RAM.

---

## ✨ Features

| Feature | Status |
|---|---|
| `@app.get / post / put / patch / delete / options / head` | ✅ |
| URL converters `<name>` `<int:n>` `<float:n>` `<path:p>` | ✅ |
| `request.args / form / files / json / cookies / headers` | ✅ |
| `jsonify()` `redirect()` `make_response()` `abort()` `send_file()` | ✅ |
| `response.set_cookie()` `delete_cookie()` `set_header()` | ✅ |
| CORS with preflight, credentials, `Vary: Origin` | ✅ |
| Blueprints with `url_prefix` and per-blueprint hooks | ✅ |
| `before_request / after_request / teardown_request` | ✅ |
| `@app.errorhandler(404)` / `@app.errorhandler(ValueError)` | ✅ |
| 12 named `HTTPException` subclasses | ✅ |
| Jinja2-compatible template engine (no `eval`) | ✅ |
| Structured logger (levels, file, ANSI colour, named loggers) | ✅ |
| Static file serving `/static/<path:filename>` | ✅ |
| Debug HTML error page with traceback | ✅ |
| Multipart form-data / file upload | ✅ |
| `url_for()` reverse routing | ✅ |
| Async uasyncio server | ✅ |

---

## 📦 Installation

### On Raspberry Pi Pico W (MicroPython)

Upload the `uflask/` folder to your Pico W using [Thonny](https://thonny.org/),
[mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html), or
[rshell](https://github.com/dhylands/rshell):

```bash
# Using mpremote
mpremote connect /dev/ttyUSB0 cp -r uflask/ :uflask/
```

### On CPython (development / testing)

```bash
pip install uflask
# or for development with extras:
pip install uflask[dev]
```

### From source

```bash
git clone https://github.com/bishek/uflask
cd uflask
pip install -e ".[dev]"
```

---

## 🚀 Quick Start

### REST API

```python
from uflask import UFlask, jsonify, abort

app = UFlask(__name__, debug=True)

users = {1: {"id": 1, "name": "Alice"}}

@app.get("/api/users")
def list_users(request):
    return jsonify(list(users.values()))

@app.get("/api/users/<int:uid>")
def get_user(request, uid):
    user = users.get(uid)
    if not user:
        abort(404, "User not found")
    return jsonify(user)

@app.post("/api/users")
def create_user(request):
    data = request.get_json()
    if not data or not data.get("name"):
        abort(400, "'name' is required")
    uid = max(users) + 1
    users[uid] = {"id": uid, "name": data["name"]}
    return jsonify(users[uid]), 201

app.run()
```

### Server-Side Rendering

```python
from uflask import UFlask, render_template, redirect, make_response

app = UFlask(__name__)

@app.get("/login")
def login_page(request):
    return render_template("login.html", title="Login", error="")

@app.post("/login")
def login(request):
    if request.form.get("password") == "secret":
        resp = make_response()
        resp.set_cookie("session", "token-abc", httponly=True, max_age=3600)
        resp.status = 302
        resp.headers["Location"] = "/dashboard"
        return resp
    return render_template("login.html", title="Login", error="Wrong password"), 401
```

### CORS

```python
from uflask import UFlask, CORS

app = UFlask(__name__)
CORS(app, origins=["https://myfrontend.com"], credentials=True)
```

### Blueprints

```python
# sensors.py
from uflask import Blueprint, jsonify

bp = Blueprint("sensors", url_prefix="/api/v1")

@bp.get("/temperature")
def temperature(request):
    return jsonify({"celsius": 24.5})

# main.py
from uflask import UFlask
from sensors import bp

app = UFlask(__name__)
app.register_blueprint(bp)
app.run()
```

### Middleware & Hooks

```python
@app.before_request
def require_auth(request):
    if request.path.startswith("/api/") and not request.headers.get("authorization"):
        from uflask import abort
        abort(401)

@app.after_request
def add_headers(request, response):
    response.headers["X-Powered-By"] = "uFlask"
    return response

@app.teardown_request
def cleanup(request, exc):
    if exc:
        print("Error during request:", exc)
```

### Custom Error Handlers

```python
@app.errorhandler(404)
def not_found(exc):
    return jsonify({"error": str(exc), "status": 404}), 404

@app.errorhandler(ValueError)
def validation_error(exc):
    return jsonify({"error": "Validation failed", "detail": str(exc)}), 400
```

### Template Syntax

```html
<!-- templates/index.html -->
<h1>{{ title }}</h1>

{% if user.role == "admin" %}
  <p>Welcome, administrator!</p>
{% elif user.role == "mod" %}
  <p>Welcome, moderator!</p>
{% else %}
  <p>Welcome, {{ user.name }}!</p>
{% endif %}

<ul>
{% for item in items %}
  <li>{{ loop.index }}. {{ item.name }}</li>
{% endfor %}
</ul>

{# This is a comment and will not appear in output #}
<p>Raw HTML: {{ content | raw }}</p>
```

---

## 📂 Project Layout

```
uflask/                    ← project root (this directory)
│
├── uflask/                ← Python package (upload this folder to Pico W)
│   ├── __init__.py        ← public API surface
│   ├── app.py             ← UFlask core: routing, server, lifecycle
│   ├── request.py         ← Request, MultiDict, parsers
│   ├── response.py        ← Response, FileResponse, helpers
│   ├── exceptions.py      ← HTTPException hierarchy + ErrorHandlerRegistry
│   ├── middleware.py      ← before/after/teardown hook stack
│   ├── cors.py            ← CORS integration
│   ├── template.py        ← Jinja2-compatible template engine
│   ├── blueprints.py      ← Blueprint class
│   ├── logging.py         ← structured logger
│   └── py.typed           ← PEP 561 marker
│
├── examples/
│   └── main.py            ← full demo (REST API + SSR + auth + sensors)
│
├── templates_example/     ← example HTML templates for the demo
│   └── templates/
│       ├── login.html
│       └── dashboard.html
│
├── tests/
│   ├── __init__.py
│   ├── test_request.py
│   ├── test_response.py
│   ├── test_routing.py
│   ├── test_template.py
│   ├── test_cors.py
│   ├── test_middleware.py
│   └── test_exceptions.py
│
├── docs/
│   ├── index.md
│   ├── quickstart.md
│   ├── routing.md
│   ├── request.md
│   ├── response.md
│   ├── templates.md
│   ├── blueprints.md
│   ├── middleware.md
│   ├── cors.md
│   ├── exceptions.md
│   └── logging.md
│
├── pyproject.toml         ← build system + project metadata (PEP 517/621)
├── setup.cfg              ← legacy setuptools compatibility
├── MANIFEST.in            ← sdist file inclusion rules
├── CHANGELOG.md           ← version history
├── LICENSE                ← MIT licence
└── README.md              ← this file
```

---

## ⚙️ Configuration

```python
app = UFlask(
    __name__,
    host          = "0.0.0.0",   # bind address
    port          = 80,           # TCP port
    debug         = False,        # True → pretty HTML tracebacks
    static_dir    = "static",     # filesystem dir for static files
    static_url    = "/static",    # URL prefix for static files
    max_body_size = 8192,         # max request body bytes (default 8 kB)
    backlog       = 5,            # TCP listen backlog
)

# Runtime config store
app.config["DB_URL"] = "sqlite:///data.db"
app.config["SECRET"] = "my-secret-key"
```

### Logging

```python
from uflask import logging, getLogger

logging.set_level(logging.DEBUG)        # DEBUG / INFO / WARNING / ERROR / CRITICAL
logging.set_log_file("/log.txt")        # optional file output
logging.enable_color(True)              # ANSI colour (terminal only)

log = getLogger("mymodule")
log.info("Server started")
log.exception("Crash!", exc)
```

---

## 🔌 Pico W Wi-Fi Setup

```python
import network, time

def connect(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    for _ in range(20):
        if wlan.isconnected():
            print("Connected:", wlan.ifconfig()[0])
            return
        time.sleep(1)
    raise RuntimeError("Wi-Fi failed")

connect("YOUR_SSID", "YOUR_PASSWORD")

from uflask import UFlask, jsonify
app = UFlask(__name__)

@app.get("/")
def index(request):
    return jsonify({"hello": "pico"})

app.run()
```

---

## 🧪 Running Tests (CPython)

```bash
pip install uflask[dev]
pytest
pytest --cov=uflask --cov-report=term-missing
```

---

## 📦 Building & Publishing

```bash
# Build wheel + sdist
python -m build

# Check the distribution
twine check dist/*

# Upload to PyPI
twine upload dist/*
```

---

## 🗺️ Roadmap

- [ ] WebSocket support
- [ ] Rate-limiting middleware
- [ ] Session middleware (cookie-based HMAC)
- [ ] JSON schema validation helper
- [ ] `mip` / `upip` package registry entry
- [ ] mkdocs documentation site

---

## 📄 License

MIT © 2026 Bishek — see [LICENSE](LICENSE)
