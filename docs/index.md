# uFlask

> **A Flask-compatible micro web framework for MicroPython on the Raspberry Pi Pico W**

<div style="display:flex;gap:.5rem;flex-wrap:wrap;margin:1rem 0">
  <img src="https://img.shields.io/badge/version-1.0.0-cyan" alt="version">
  <img src="https://img.shields.io/badge/MicroPython-1.22%2B-blue" alt="micropython">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="license">
  <img src="https://img.shields.io/badge/platform-Pico%20W-orange" alt="platform">
</div>

---

uFlask lets you write web servers on the **Raspberry Pi Pico W** using the same API you already know from **Flask** — decorators, request objects, Jinja2-style templates, Blueprints, middleware hooks, CORS, and structured logging — in **pure MicroPython**, with **zero external dependencies**.

```python
from uflask import UFlask, jsonify

app = UFlask(__name__, debug=True)

@app.get("/")
def index(request):
    return jsonify({"hello": "pico", "status": "running"})

@app.get("/users/<int:uid>")
def get_user(request, uid):
    return jsonify({"id": uid, "name": "Alice"})

app.run()
```

---

## Why uFlask?

| Problem | uFlask Solution |
|---|---|
| MicroPython has no built-in web framework | Full async HTTP/1.1 server via `uasyncio` |
| Writing raw socket code is tedious | Flask-style decorators and helpers |
| Debugging on hardware is painful | `debug=True` → styled HTML tracebacks |
| Managing multiple route files is messy | Blueprints — split app into modules |
| Cross-origin requests are blocked | Built-in CORS with preflight support |
| Template strings are error-prone | Jinja2-compatible template engine |

---

## Feature Overview

=== "Routing"
    ```python
    @app.get("/items")
    @app.post("/items")
    @app.put("/items/<int:id>")
    @app.delete("/items/<int:id>")
    @app.route("/data", methods=["GET","POST"])
    ```

=== "Request"
    ```python
    request.args["page"]          # query params
    request.form["username"]      # form data
    request.get_json()            # JSON body
    request.cookies["session"]    # cookies
    request.headers["x-api-key"]  # headers
    request.files["upload"]       # file upload
    ```

=== "Response"
    ```python
    return jsonify({"ok": True})
    return redirect("/login")
    return send_file("/data.csv")
    return make_response("text", 200)
    abort(403, "No access")
    ```

=== "Templates"
    ```html
    <h1>{{ title }}</h1>
    {% if user.role == "admin" %}
      <span>Admin panel</span>
    {% endif %}
    {% for item in items %}
      <li>{{ loop.index }}. {{ item.name }}</li>
    {% endfor %}
    ```

---

## Quick Navigation

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem;margin-top:1rem">

<div style="border:1px solid #334155;border-radius:8px;padding:1rem">
<strong>🚀 <a href="quickstart/">Quick Start</a></strong><br>
Build your first REST API in 5 minutes
</div>

<div style="border:1px solid #334155;border-radius:8px;padding:1rem">
<strong>📦 <a href="installation/">Installation</a></strong><br>
Get uFlask on your Pico W or CPython
</div>

<div style="border:1px solid #334155;border-radius:8px;padding:1rem">
<strong>🔀 <a href="routing/">Routing</a></strong><br>
URL rules, converters, HTTP methods
</div>

<div style="border:1px solid #334155;border-radius:8px;padding:1rem">
<strong>📥 <a href="request/">Request</a></strong><br>
Full request object reference
</div>

<div style="border:1px solid #334155;border-radius:8px;padding:1rem">
<strong>📤 <a href="response/">Response</a></strong><br>
JSON, redirects, files, cookies
</div>

<div style="border:1px solid #334155;border-radius:8px;padding:1rem">
<strong>🖼️ <a href="templates/">Templates</a></strong><br>
Server-side HTML rendering
</div>

<div style="border:1px solid #334155;border-radius:8px;padding:1rem">
<strong>🧩 <a href="blueprints/">Blueprints</a></strong><br>
Split app into modules
</div>

<div style="border:1px solid #334155;border-radius:8px;padding:1rem">
<strong>🪝 <a href="middleware/">Middleware</a></strong><br>
before/after/teardown hooks
</div>

<div style="border:1px solid #334155;border-radius:8px;padding:1rem">
<strong>🌐 <a href="cors/">CORS</a></strong><br>
Cross-origin resource sharing
</div>

<div style="border:1px solid #334155;border-radius:8px;padding:1rem">
<strong>⚠️ <a href="exceptions/">Error Handling</a></strong><br>
HTTP exceptions and error handlers
</div>

<div style="border:1px solid #334155;border-radius:8px;padding:1rem">
<strong>📋 <a href="logging/">Logging</a></strong><br>
Structured log levels and file output
</div>

<div style="border:1px solid #334155;border-radius:8px;padding:1rem">
<strong>🚢 <a href="deployment/">Deployment</a></strong><br>
Pico W Wi-Fi setup and production tips
</div>

</div>

---

## What's Inside

```
uflask/              ← the Python package
├── app.py           ← UFlask core (async server, routing, lifecycle)
├── request.py       ← Request object + MultiDict + body parsers
├── response.py      ← Response, FileResponse, jsonify, redirect…
├── exceptions.py    ← HTTPException hierarchy + ErrorHandlerRegistry
├── middleware.py    ← before/after/teardown hook stack
├── cors.py          ← CORS with preflight + Vary header
├── template.py      ← Jinja2-compatible template engine (no eval)
├── blueprints.py    ← Blueprint class
├── logging.py       ← structured logger with levels + file output
└── _compat.py       ← MicroPython ↔ CPython compatibility shim
```

---

## License

MIT © 2026 Bishek
