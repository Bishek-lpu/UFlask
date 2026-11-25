# Quick Start

Build a working REST API and an HTML web page in under 5 minutes.

---

## Step 1 — Connect to Wi-Fi

Every web server needs a network. Add this to the top of `main.py`:

```python
import network
import time

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        print("Already connected:", wlan.ifconfig()[0])
        return
    print("Connecting to", ssid, "…")
    wlan.connect(ssid, password)
    for _ in range(20):          # wait up to 20 seconds
        if wlan.isconnected():
            print("Connected! IP:", wlan.ifconfig()[0])
            return
        time.sleep(1)
    raise RuntimeError("Wi-Fi failed — check your SSID and password")

connect_wifi("YOUR_SSID", "YOUR_PASSWORD")
```

---

## Step 2 — Create the App

```python
from uflask import UFlask, jsonify, render_template

app = UFlask(__name__, debug=True)
```

| Parameter | Default | Description |
|---|---|---|
| `__name__` | — | Application name (use `__name__`) |
| `debug` | `False` | Show HTML tracebacks on errors |
| `host` | `"0.0.0.0"` | Bind to all network interfaces |
| `port` | `80` | HTTP port |

---

## Step 3 — Your First Route

```python
@app.get("/")
def home(request):
    return jsonify({
        "name":    "uFlask",
        "version": "1.0.0",
        "status":  "running",
    })
```

Visit `http://<pico-ip>/` in your browser and you'll see:

```json
{
  "name": "uFlask",
  "version": "1.0.0",
  "status": "running"
}
```

---

## Step 4 — Add URL Parameters

```python
# Simple string parameter
@app.get("/greet/<name>")
def greet(request, name):
    return jsonify({"message": "Hello, %s!" % name})

# Integer parameter — automatically converted
@app.get("/square/<int:n>")
def square(request, n):
    return jsonify({"input": n, "result": n * n})
```

| URL | Response |
|---|---|
| `/greet/Alice` | `{"message": "Hello, Alice!"}` |
| `/square/7` | `{"input": 7, "result": 49}` |

---

## Step 5 — Read Request Data

```python
# Query string:  GET /search?q=pico&limit=5
@app.get("/search")
def search(request):
    query = request.args.get("q", "")
    limit = int(request.args.get("limit", 10))
    return jsonify({"query": query, "limit": limit})

# JSON body:  POST /echo  {"key": "value"}
@app.post("/echo")
def echo(request):
    data = request.get_json()          # returns dict or None
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    return jsonify({"you_sent": data})

# Form data:  POST /submit  (HTML form)
@app.post("/submit")
def submit(request):
    name  = request.form.get("name", "")
    email = request.form.get("email", "")
    return jsonify({"name": name, "email": email})
```

---

## Step 6 — Server-Side HTML

Create a template file at `templates/hello.html`:

```html
<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
  <h1>Hello, {{ name }}!</h1>
  <p>Items:</p>
  <ul>
    {% for item in items %}
      <li>{{ loop.index }}. {{ item }}</li>
    {% endfor %}
  </ul>
</body>
</html>
```

Then in your route:

```python
@app.get("/hello")
def hello_page(request):
    html = render_template(
        "hello.html",
        title = "My Pico Page",
        name  = "World",
        items = ["Sensor data", "GPIO control", "Wi-Fi"],
    )
    return html, 200, "text/html; charset=utf-8"
```

---

## Step 7 — Error Handling

```python
from uflask import abort, NotFound

users = {1: "Alice", 2: "Bob"}

@app.get("/users/<int:uid>")
def get_user(request, uid):
    if uid not in users:
        abort(404, "User %d not found" % uid)
    return jsonify({"id": uid, "name": users[uid]})

# Custom handler for 404
@app.errorhandler(404)
def not_found(exc):
    return jsonify({"error": str(exc)}), 404
```

---

## Step 8 — Run the Server

```python
app.run()
```

That's it! The full minimal `main.py`:

```python
import network, time
from uflask import UFlask, jsonify

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

app = UFlask(__name__, debug=True)

@app.get("/")
def index(request):
    return jsonify({"hello": "pico"})

app.run()
```

---

## What's Next?

- [Routing](routing.md) — URL converters, multiple methods, Blueprints
- [Request Object](request.md) — query params, JSON, forms, cookies
- [Response Helpers](response.md) — JSON, files, cookies, redirects
- [Templates](templates.md) — full Jinja2-style syntax guide
- [Deployment](deployment.md) — production tips for the Pico W
