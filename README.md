<div align="center">

<img src="https://raw.githubusercontent.com/Bishek-lpu/UFlask/main/docs/assets/banner.svg" alt="uFlask Banner" width="100%">

# ⚡ uFlask

### Flask-compatible micro web framework for MicroPython
### *Raspberry Pi Pico W · Zero dependencies · Pure Python*

<br>

[![PyPI Version](https://img.shields.io/badge/version-1.0.0-00b4d8?style=for-the-badge&logo=python&logoColor=white)](https://pypi.org/project/uflask/)
[![MicroPython](https://img.shields.io/badge/MicroPython-1.22%2B-2b9348?style=for-the-badge&logo=micropython&logoColor=white)](https://micropython.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-f9c74f?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Pico%20W-e63946?style=for-the-badge&logo=raspberrypi&logoColor=white)](https://www.raspberrypi.com/products/raspberry-pi-pico/)
[![Stars](https://img.shields.io/github/stars/Bishek-lpu/UFlask?style=for-the-badge&color=ff9f1c)](https://github.com/Bishek-lpu/UFlask/stargazers)

<br>

[📖 Docs](https://github.com/Bishek-lpu/UFlask/tree/main/docs) · [🚀 Quick Start](#-quick-start) · [💡 Examples](examples/) · [🐛 Issues](https://github.com/Bishek-lpu/UFlask/issues) · [📦 Changelog](CHANGELOG.md)

</div>

---

## 🌟 What is uFlask?

**uFlask** brings the **Flask developer experience** to the **Raspberry Pi Pico W**. Write REST APIs and server-side rendered web pages with the same decorators, request objects, and helpers you already know — in pure MicroPython, with zero external dependencies.

```python
from uflask import UFlask, jsonify

app = UFlask(__name__, debug=True)

@app.get("/")
def index(request):
    return jsonify({"hello": "pico", "status": "🟢 running"})

@app.get("/sensor/<int:id>")
def sensor(request, id):
    return jsonify({"id": id, "temperature": 24.5, "humidity": 61.0})

app.run()
```

---

## ✨ Feature Highlights

<table>
<tr>
<td width="50%">

**🔀 Routing**
```python
@app.get("/items")
@app.post("/items")
@app.put("/items/<int:id>")
@app.delete("/items/<int:id>")
@app.route("/data", methods=["GET","POST"])
```

</td>
<td width="50%">

**📥 Request Object**
```python
request.args["page"]        # query params
request.form["username"]    # form data
request.get_json()          # JSON body
request.cookies["session"]  # cookies
request.files["upload"]     # file upload
```

</td>
</tr>
<tr>
<td>

**📤 Response Helpers**
```python
return jsonify({"ok": True}, status=201)
return redirect("/login")
return send_file("/export.csv")
return make_response().set_cookie("s","tok")
abort(403, "Access denied")
```

</td>
<td>

**🖼️ Jinja2 Templates**
```html
<h1>{{ title }}</h1>
{% if user.role == "admin" %}
  <a href="/admin">Panel</a>
{% endif %}
{% for item in items %}
  <li>{{ loop.index }}. {{ item.name }}</li>
{% endfor %}
```

</td>
</tr>
<tr>
<td>

**🧩 Blueprints**
```python
api = Blueprint("api", url_prefix="/api")

@api.get("/users")
def users(request): ...

app.register_blueprint(api)
# → GET /api/users
```

</td>
<td>

**🪝 Middleware Hooks**
```python
@app.before_request
def auth(request):
    if not request.cookies.get("session"):
        return redirect("/login")

@app.after_request
def headers(request, response):
    response.headers["X-Frame-Options"] = "DENY"
    return response
```

</td>
</tr>
<tr>
<td>

**🌐 CORS**
```python
CORS(app,
  origins=["https://frontend.com"],
  credentials=True,
  max_age=3600,
)
```

</td>
<td>

**⚠️ Error Handling**
```python
@app.errorhandler(404)
def not_found(exc):
    return jsonify({"error": str(exc)}), 404

@app.errorhandler(ValueError)
def val_error(exc):
    return jsonify({"error": str(exc)}), 400
```

</td>
</tr>
</table>

---

## 🗂️ Project Structure

```
UFlask/
│
├── 📦 uflask/                  ← Python package (upload this to Pico W)
│   ├── __init__.py             ← public API
│   ├── app.py                  ← async HTTP server + routing engine
│   ├── request.py              ← Request object + MultiDict + body parsers
│   ├── response.py             ← Response, FileResponse, jsonify, redirect…
│   ├── exceptions.py           ← HTTPException hierarchy + error registry
│   ├── middleware.py           ← before/after/teardown hook stack
│   ├── cors.py                 ← CORS with preflight + Vary header
│   ├── template.py             ← Jinja2-compatible template engine
│   ├── blueprints.py           ← Blueprint class
│   ├── logging.py              ← structured logger
│   └── _compat.py              ← MicroPython ↔ CPython shim
│
├── 📂 examples/
│   └── main.py                 ← full demo (REST + SSR + auth + sensors)
│
├── 📂 templates_example/       ← HTML templates for the demo app
│   └── templates/
│       ├── login.html
│       └── dashboard.html
│
├── 🧪 tests/                   ← pytest test suite (CPython)
│   ├── test_request.py
│   ├── test_response.py
│   ├── test_routing.py
│   ├── test_template.py
│   ├── test_cors.py
│   └── test_exceptions.py
│
├── 📚 docs/                    ← MkDocs documentation (15 pages)
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
│   ├── logging.md
│   ├── deployment.md
│   └── api-reference.md
│
├── pyproject.toml              ← build config (PEP 517/621)
├── setup.cfg                   ← legacy pip compatibility
├── MANIFEST.in                 ← sdist rules
├── mkdocs.yml                  ← docs site config
├── CHANGELOG.md
├── LICENSE (MIT)
└── README.md
```

---

## 🚀 Quick Start

### Step 1 — Upload to Pico W

```bash
# Using mpremote
pip install mpremote
mpremote connect /dev/ttyUSB0 cp -r uflask/ :uflask/
mpremote connect /dev/ttyUSB0 cp examples/main.py :main.py
```

### Step 2 — Connect to Wi-Fi

```python
import network, time

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    for _ in range(20):
        if wlan.isconnected():
            print("IP:", wlan.ifconfig()[0])
            return
        time.sleep(1)
    raise RuntimeError("Wi-Fi failed")

connect_wifi("YOUR_SSID", "YOUR_PASSWORD")
```

### Step 3 — Write Your App

```python
from uflask import UFlask, jsonify, render_template, CORS, abort

app = UFlask(__name__, debug=True)
CORS(app, origins="*")

# ── REST API ──────────────────────────────────────────
items = {}

@app.get("/api/items")
def list_items(request):
    return jsonify(list(items.values()))

@app.get("/api/items/<int:id>")
def get_item(request, id):
    item = items.get(id)
    if not item:
        abort(404, "Item %d not found" % id)
    return jsonify(item)

@app.post("/api/items")
def create_item(request):
    data = request.get_json()
    if not data or not data.get("name"):
        abort(400, "'name' is required")
    id = len(items) + 1
    items[id] = {"id": id, "name": data["name"]}
    return jsonify(items[id]), 201

# ── Error handlers ────────────────────────────────────
@app.errorhandler(404)
def not_found(exc):
    return jsonify({"error": str(exc)}), 404

@app.errorhandler(400)
def bad_request(exc):
    return jsonify({"error": str(exc)}), 400

# ── Run ───────────────────────────────────────────────
app.run()
```

---

## 📡 REST API Cheat Sheet

| Method | URL | Action |
|--------|-----|--------|
| `GET` | `/api/items` | List all items |
| `GET` | `/api/items/1` | Get item by ID |
| `POST` | `/api/items` | Create new item |
| `PUT` | `/api/items/1` | Replace item |
| `PATCH` | `/api/items/1` | Update fields |
| `DELETE` | `/api/items/1` | Delete item |

---

## 🌐 URL Converters

| Syntax | Type | Example URL | Parameter |
|--------|------|-------------|-----------|
| `<name>` | `str` | `/users/alice` | `"alice"` |
| `<int:id>` | `int` | `/items/42` | `42` |
| `<float:val>` | `float` | `/temp/36.6` | `36.6` |
| `<path:filename>` | `str` (with `/`) | `/files/css/main.css` | `"css/main.css"` |

---

## 📦 Installation

### On Raspberry Pi Pico W (MicroPython)
```bash
# Upload with mpremote
mpremote connect /dev/ttyUSB0 cp -r uflask/ :uflask/
```

### On CPython (dev/testing)
```bash
git clone https://github.com/Bishek-lpu/UFlask.git
cd UFlask
pip install -e ".[dev]"
```

---

## 🧪 Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| [Quick Start](docs/quickstart.md) | Build your first API in 5 minutes |
| [Routing](docs/routing.md) | URL rules, converters, blueprints |
| [Request Object](docs/request.md) | Query, form, JSON, cookies, files |
| [Response Helpers](docs/response.md) | JSON, redirect, file, cookies |
| [Templates](docs/templates.md) | Jinja2-style server-side rendering |
| [Blueprints](docs/blueprints.md) | Split app into modules |
| [Middleware](docs/middleware.md) | before/after/teardown hooks |
| [CORS](docs/cors.md) | Cross-origin resource sharing |
| [Error Handling](docs/exceptions.md) | HTTP exceptions & custom handlers |
| [Logging](docs/logging.md) | Structured logs, file output, colours |
| [Deployment](docs/deployment.md) | Pico W production tips |
| [API Reference](docs/api-reference.md) | Full method & class reference |

---

## ⚙️ Configuration

```python
app = UFlask(
    __name__,
    host          = "0.0.0.0",   # bind address
    port          = 80,           # TCP port
    debug         = False,        # True → HTML tracebacks (dev only!)
    static_dir    = "static",     # static file directory
    static_url    = "/static",    # static file URL prefix
    max_body_size = 8192,         # max request body (bytes)
    backlog       = 5,            # TCP listen backlog
)
```

---

## 🔌 Pico W Specifications

| Property | Value |
|----------|-------|
| MCU | RP2040 (dual-core ARM Cortex-M0+) |
| RAM | 264 kB SRAM |
| Flash | 2 MB |
| Wi-Fi | 2.4 GHz 802.11 b/g/n (CYW43439) |
| MicroPython | 1.22+ |
| uFlask RAM usage | ~40–80 kB (depends on routes) |

---

## 🗺️ Roadmap

- [ ] WebSocket support
- [ ] Rate-limiting middleware
- [ ] Cookie-based session manager (HMAC)
- [ ] JSON schema request validator
- [ ] `mip` / `upip` package registry entry
- [ ] GitHub Actions CI badge (live tests)
- [ ] MkDocs site hosted on GitHub Pages

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'feat: add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

Please read [CONTRIBUTING.md](.github/CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT © 2026 [Bishek](https://github.com/Bishek-lpu)

<div align="center">

---

**Made with ❤️ for the MicroPython & IoT community**

*If this project helped you, please consider giving it a ⭐*

[![GitHub stars](https://img.shields.io/github/stars/Bishek-lpu/UFlask?style=social)](https://github.com/Bishek-lpu/UFlask/stargazers)

</div>
