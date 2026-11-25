# Logging

uFlask includes a structured logger designed to work within the memory constraints of the Raspberry Pi Pico W. It mirrors Python's standard `logging` module API.

---

## Quick Start

```python
from uflask import logging

logging.info("Server started")
logging.warning("Low memory!")
logging.error("Connection failed")
logging.debug("Parsed body: %s" % data)
```

Each line prints:

```
2026-11-25 14:32:01 [INFO       124kB] Server started
2026-11-25 14:32:05 [WARNING    118kB] Low memory!
```

Format: `timestamp [LEVEL  free_ram] message`

---

## Log Levels

| Level | Constant | Use for |
|---|---|---|
| `DEBUG` | `10` | Detailed diagnostic info (dev only) |
| `INFO` | `20` | Normal operational events |
| `WARNING` | `30` | Unexpected but recoverable situations |
| `ERROR` | `40` | Serious failures |
| `CRITICAL` | `50` | Fatal errors (server about to crash) |

---

## Setting the Minimum Level

Only messages at or above the configured level are emitted.

```python
from uflask import logging

# Development: see everything
logging.set_level(logging.DEBUG)

# Production: only important events
logging.set_level(logging.WARNING)

# Or use the constant values
logging.set_level(10)   # DEBUG
logging.set_level(20)   # INFO
logging.set_level(30)   # WARNING
logging.set_level(40)   # ERROR
```

uFlask sets the level automatically based on `debug`:

```python
app = UFlask(__name__, debug=True)   # → DEBUG
app = UFlask(__name__, debug=False)  # → INFO
```

---

## Logging Functions

```python
from uflask import logging

logging.debug("Parsing body:", request.data)
logging.info("User created:", user["name"])
logging.warning("Memory low, GC running…")
logging.error("DB write failed:", exc)
logging.critical("Out of memory — halting")

# Log with an exception traceback
try:
    risky_operation()
except Exception as e:
    logging.exception("risky_operation failed", e)
    # Prints the error message + full Python traceback
```

---

## Named Loggers

Create a named logger for each module to easily identify where messages come from:

```python
# sensors.py
from uflask import getLogger

log = getLogger("sensors")

log.info("Temperature read: 24.5°C")
# → 2026-11-25 14:32:01 [INFO        98kB] [sensors] Temperature read: 24.5°C
```

Named loggers support all the same methods as the global logger:

```python
log = getLogger("auth")

log.debug("Login attempt for user:", username)
log.info("Login successful:", username)
log.warning("Failed login attempt:", username)
log.error("Auth service error:", exc)
log.exception("Unhandled auth error", exc)
```

### Setting level per logger

```python
log = getLogger("sensors")
log.set_level(logging.WARNING)   # only warnings and above for this logger
```

---

## File Logging

Persist logs to a file on the Pico W's filesystem:

```python
logging.set_log_file("/log.txt")
```

Now every log message is written to both `stdout` (serial REPL) **and** `/log.txt`.

```python
# Rotate log (read and clear)
def read_and_clear_log():
    try:
        with open("/log.txt") as f:
            content = f.read()
        import os
        os.remove("/log.txt")
        return content
    except OSError:
        return ""

@app.get("/admin/logs")
def get_logs(request):
    return read_and_clear_log(), 200, "text/plain"
```

> **Note:** The Pico W has 2 MB of flash. Rotate or clear logs regularly to avoid running out of space.

---

## ANSI Colour Output

If your terminal supports ANSI colours (most do), enable colour output for easier reading:

```python
logging.enable_color(True)
```

| Level | Colour |
|---|---|
| DEBUG | Cyan |
| INFO | Green |
| WARNING | Yellow |
| ERROR | Red |
| CRITICAL | Magenta |

---

## Integration with the App

uFlask uses the logger internally. You'll see output like:

```
2026-11-25 14:32:00 [INFO       124kB] uFlask 1.0.0 | myapp | 0.0.0.0:80 | debug=True
2026-11-25 14:32:00 [INFO       124kB] Listening on http://0.0.0.0:80
2026-11-25 14:32:05 [INFO       120kB] 192.168.1.42 GET /api/users → 200 [12ms] curl/7.88
2026-11-25 14:32:06 [INFO       118kB] Blueprint 'sensors' registered (prefix='/sensors', routes=3)
2026-11-25 14:32:10 [ERROR      112kB] Unhandled exception during request
```

---

## Logging in Middleware

```python
from uflask import getLogger

log = getLogger("middleware")

@app.before_request
def log_request(request):
    log.debug("→ %s %s from %s" % (
        request.method,
        request.path,
        request.remote_addr or "?",
    ))

@app.after_request
def log_response(request, response):
    level = logging.WARNING if response.status >= 400 else logging.INFO
    log._emit(level, "← %d %s" % (response.status, request.path))
    return response

@app.teardown_request
def log_error(request, exc):
    if exc:
        log.exception("Teardown error on %s %s" % (request.method, request.path), exc)
```

---

## Logger API Reference

| Function / Method | Description |
|---|---|
| `logging.set_level(level)` | Set global minimum level |
| `logging.set_log_file(path)` | Enable file logging (None to disable) |
| `logging.enable_color(True)` | Enable ANSI colour output |
| `logging.debug(*items)` | Log at DEBUG |
| `logging.info(*items)` | Log at INFO |
| `logging.warning(*items)` | Log at WARNING |
| `logging.error(*items)` | Log at ERROR |
| `logging.critical(*items)` | Log at CRITICAL |
| `logging.exception(msg, exc)` | Log at ERROR + print traceback |
| `getLogger(name)` | Create a named logger |
| `Logger.set_level(level)` | Override level for this logger |
| `Logger.debug/info/…(*items)` | Same as global functions |
| `Logger.exception(msg, exc)` | Same as global exception |

### Level Constants

```python
logging.DEBUG    = 10
logging.INFO     = 20
logging.WARNING  = 30
logging.ERROR    = 40
logging.CRITICAL = 50
```
