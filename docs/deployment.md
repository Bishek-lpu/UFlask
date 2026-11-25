# Deployment

This guide covers everything you need to run uFlask reliably on a **Raspberry Pi Pico W** in a production environment.

---

## Wi-Fi Connection

Always wait for a solid Wi-Fi connection before starting the server. Use this robust helper:

```python
import network
import time

def connect_wifi(ssid, password, retries=3, timeout=20):
    """
    Connect to Wi-Fi with retry logic.
    Returns the IP address on success, raises RuntimeError on failure.
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    for attempt in range(1, retries + 1):
        print("Wi-Fi attempt %d/%d…" % (attempt, retries))
        wlan.connect(ssid, password)

        for _ in range(timeout):
            if wlan.isconnected():
                ip = wlan.ifconfig()[0]
                print("✓ Connected. IP:", ip)
                return ip
            time.sleep(1)

        wlan.disconnect()
        time.sleep(2)

    raise RuntimeError("Wi-Fi connection failed after %d attempts" % retries)
```

---

## Auto-start on Boot

MicroPython runs `main.py` automatically at boot. Structure your `main.py`:

```python
# main.py
import network, time

WIFI_SSID     = "YOUR_SSID"
WIFI_PASSWORD = "YOUR_PASSWORD"

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    for _ in range(20):
        if wlan.isconnected():
            return wlan.ifconfig()[0]
        time.sleep(1)
    raise RuntimeError("Wi-Fi failed")

# Connect first
ip = connect_wifi(WIFI_SSID, WIFI_PASSWORD)
print("Server at http://%s" % ip)

# Then start the app
from uflask import UFlask, jsonify

app = UFlask(__name__, debug=False)   # debug=False in production!

@app.get("/")
def index(request):
    return jsonify({"status": "ok"})

app.run()
```

---

## Production Settings

```python
app = UFlask(
    __name__,
    debug         = False,   # ← always False in production
    max_body_size = 8192,    # 8 kB — increase only if needed
    backlog       = 3,       # Pico W can handle ~3 concurrent connections
)
```

### Key differences: dev vs production

| Setting | Development | Production |
|---|---|---|
| `debug` | `True` | **`False`** |
| `logging level` | `DEBUG` | `WARNING` or `ERROR` |
| `log file` | None | `/log.txt` |
| `max_body_size` | 16384 | 4096–8192 |
| `CORS origins` | `["http://localhost:*"]` | Explicit domain list |
| Error responses | HTML traceback | JSON `{"error": "…"}` |

---

## Memory Management

The Pico W has only **264 kB RAM** (around 180 kB free for MicroPython). Keep these tips in mind:

### Garbage collection

uFlask calls `gc.collect()` before every request automatically. For large apps, also collect in teardown:

```python
import gc

@app.teardown_request
def collect(request, exc):
    gc.collect()
```

### Monitor free RAM

```python
@app.get("/health")
def health(request):
    import gc
    gc.collect()
    return jsonify({
        "status":   "ok",
        "mem_free": gc.mem_free(),
        "mem_alloc": gc.mem_alloc(),
    })
```

### Keep responses small

```python
# ✅ Return only what the client needs
@app.get("/api/sensors")
def sensors(request):
    n = int(request.args.get("n", 10))   # limit results
    return jsonify(last_n_readings(n))

# ❌ Avoid returning all data at once
@app.get("/api/sensors")
def sensors(request):
    return jsonify(all_readings)   # could be hundreds of KB
```

### Keep templates small

Templates are read into RAM at render time. Split large templates into smaller ones and render them separately.

---

## Static Files

Serve CSS, JS, and images from the `static/` directory:

```python
app = UFlask(__name__, static_dir="static", static_url="/static")
```

uFlask streams static files in **512-byte chunks**, so even files larger than available RAM work.

```
static/
├── style.css
├── app.js
└── favicon.ico
```

Access at `http://<pico-ip>/static/style.css`.

> **Tip:** Minify CSS and JS before uploading to save flash space and reduce transfer time.

---

## Configuration File

Avoid hardcoding credentials. Use a `config.py`:

```python
# config.py  — do NOT commit to git
WIFI_SSID     = "MyNetwork"
WIFI_PASSWORD = "MyPassword"
API_SECRET    = "super-secret-key"
DEBUG         = False
LOG_FILE      = "/log.txt"
```

```python
# main.py
import config

connect_wifi(config.WIFI_SSID, config.WIFI_PASSWORD)
app = UFlask(__name__, debug=config.DEBUG)
app.config["SECRET"] = config.API_SECRET
```

---

## Watchdog Timer

The Pico W has a hardware watchdog that resets the board if the main loop hangs. Enable it in production:

```python
from machine import WDT

wdt = WDT(timeout=8000)   # reset if not fed within 8 seconds

@app.after_request
def feed_watchdog(request, response):
    wdt.feed()
    return response
```

---

## Logging to Flash

```python
from uflask import logging

logging.set_level(logging.WARNING)   # only warnings and above
logging.set_log_file("/log.txt")     # write to flash

# Serve logs via a protected endpoint
@app.get("/admin/log")
def get_log(request):
    if request.headers.get("x-admin-key") != app.config["SECRET"]:
        from uflask import abort
        abort(403)
    try:
        with open("/log.txt") as f:
            return f.read(), 200, "text/plain"
    except OSError:
        return "No log file", 404

@app.delete("/admin/log")
def clear_log(request):
    if request.headers.get("x-admin-key") != app.config["SECRET"]:
        from uflask import abort
        abort(403)
    import os
    try:
        os.remove("/log.txt")
    except OSError:
        pass
    return jsonify({"cleared": True})
```

---

## Finding the Pico W's IP Address

```python
import network

wlan = network.WLAN(network.STA_IF)
print(wlan.ifconfig())
# → ('192.168.1.42', '255.255.255.0', '192.168.1.1', '8.8.8.8')
```

For a fixed IP, use mDNS (via your router) or configure a **DHCP reservation** so the Pico W always gets the same IP.

---

## Uploading Files

```bash
# Upload everything at once with mpremote
mpremote connect /dev/ttyUSB0 \
    cp -r uflask/ :uflask/ \
    + cp -r static/ :static/ \
    + cp -r templates/ :templates/ \
    + cp config.py :config.py \
    + cp main.py :main.py \
    + run main.py
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `OSError: [Errno 98]` | Port 80 already in use | Soft-reset the board (Ctrl+D in REPL) |
| `MemoryError` | Too little RAM | Add `gc.collect()`, reduce body size |
| Wi-Fi keeps dropping | Weak signal | Move closer to router, use 2.4 GHz |
| Templates not found | Wrong path | Check `TEMPLATES_DIR` or use absolute path |
| `import uflask` fails | Package not uploaded | Re-upload the `uflask/` folder |
| Slow responses | Large payload | Paginate results, compress static files |
| 404 on static files | Wrong `static_dir` | Verify folder name matches `UFlask(static_dir=…)` |
