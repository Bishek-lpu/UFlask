# main.py  –  uFlask demo application for Raspberry Pi Pico W
# ===========================================================
# Demonstrates:
#   • REST API (JSON)
#   • Server-Side Rendering (HTML templates)
#   • CORS
#   • Blueprints
#   • Middleware (before_request / after_request / teardown_request)
#   • Custom error handlers
#   • Cookies & redirects
#   • Static file serving
#   • Debug mode
#   • Logging configuration
# ===========================================================

import network
import time
import uasyncio as asyncio

# ---- Wi-Fi configuration ----
WIFI_SSID     = "YOUR_SSID"
WIFI_PASSWORD = "YOUR_PASSWORD"

# ---- Connect to Wi-Fi ----
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to Wi-Fi …")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        for _ in range(20):
            if wlan.isconnected():
                break
            time.sleep(1)
    if wlan.isconnected():
        print("Wi-Fi connected:", wlan.ifconfig()[0])
    else:
        raise RuntimeError("Wi-Fi connection failed")


# ============================================================
# Import uFlask
# ============================================================

from uflask import (
    UFlask, CORS, Blueprint,
    jsonify, redirect, make_response, abort, render_template,
    NotFound, Unauthorized, BadRequest, Forbidden,
    logging, getLogger,
)

# ============================================================
# Application factory
# ============================================================

app = UFlask(
    __name__,
    host          = "0.0.0.0",
    port          = 80,
    debug         = True,          # set False in production
    static_dir    = "static",      # serve files from /static/
    max_body_size = 16384,         # 16 kB max body
)

# ---- Logging ----
logging.set_level(logging.DEBUG)   # DEBUG / INFO / WARNING / ERROR / CRITICAL
# logging.set_log_file("/log.txt") # optional file log
log = getLogger("main")

# ---- CORS ----
CORS(
    app,
    origins      = ["http://localhost:3000", "http://localhost:5173"],
    allow_headers= ["Content-Type", "Authorization", "X-Request-ID"],
    expose_headers= ["X-Total-Count"],
    credentials  = True,
    max_age      = 3600,
)

# ============================================================
# Simple in-memory "database"
# ============================================================

_users = {
    1: {"id": 1, "name": "Alice",   "email": "alice@example.com",   "role": "admin"},
    2: {"id": 2, "name": "Bob",     "email": "bob@example.com",     "role": "user"},
    3: {"id": 3, "name": "Charlie", "email": "charlie@example.com", "role": "user"},
}
_next_id = 4

# ============================================================
# Global Middleware Hooks
# ============================================================

@app.before_request
def log_request(request):
    """Log every incoming request."""
    log.debug(">>> %s %s  from=%s" % (request.method, request.path, request.remote_addr))


@app.before_request
def check_maintenance(request):
    """Example: block all non-GET in maintenance mode."""
    # Set app.config["MAINTENANCE"] = True to activate
    if app.config.get("MAINTENANCE") and request.method not in ("GET", "HEAD"):
        return jsonify({"error": "Server is in maintenance mode"}), 503


@app.after_request
def add_common_headers(request, response):
    """Add security / branding headers to every response."""
    response.headers.setdefault("X-Powered-By", "uFlask on Pico W")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    return response


@app.teardown_request
def cleanup(request, exc):
    """Called after every request, even on error."""
    if exc:
        log.warning("Request teardown with exception: %s" % exc)


@app.before_first_request
def startup():
    """Called once before the very first request."""
    log.info("🚀 First request received – startup hook running")
    app.config["started_at"] = time.time()


# ============================================================
# Custom Error Handlers
# ============================================================

@app.errorhandler(404)
def handle_404(exc):
    return jsonify({"error": "Not found", "path": "?"}), 404


@app.errorhandler(405)
def handle_405(exc):
    return jsonify({"error": str(exc)}), 405


@app.errorhandler(400)
def handle_400(exc):
    return jsonify({"error": str(exc)}), 400


@app.errorhandler(401)
def handle_401(exc):
    return jsonify({"error": "Authentication required"}), 401


@app.errorhandler(403)
def handle_403(exc):
    return jsonify({"error": "Access denied"}), 403


@app.errorhandler(500)
def handle_500(exc):
    log.exception("Internal Server Error", exc)
    return jsonify({"error": "Internal server error", "detail": str(exc)}), 500


@app.errorhandler(ValueError)
def handle_value_error(exc):
    return jsonify({"error": "Validation error", "detail": str(exc)}), 400


# ============================================================
# Health / System Routes
# ============================================================

@app.get("/")
def index(request):
    """Root – redirect to API docs."""
    return redirect("/health")


@app.get("/health")
def health(request):
    """Health check endpoint."""
    import gc
    return jsonify({
        "status":   "ok",
        "version":  app.VERSION,
        "debug":    app.debug,
        "mem_free": gc.mem_free(),
        "uptime":   time.time() - app.config.get("started_at", time.time()),
    })


@app.get("/config")
def get_config(request):
    """Return public config (admin only via X-Admin-Key header)."""
    if request.headers.get("x-admin-key") != "secret":
        raise Forbidden("Admin key required")
    return jsonify({
        "debug":         app.debug,
        "max_body_size": app.max_body_size,
        "static_url":    app.static_url,
    })


# ============================================================
# REST API – /api/users
# ============================================================

@app.get("/api/users")
def list_users(request):
    """
    GET /api/users
    GET /api/users?role=admin
    GET /api/users?page=1&per_page=2
    """
    users = list(_users.values())

    # Optional filter by role
    role = request.args.get("role")
    if role:
        users = [u for u in users if u.get("role") == role]

    # Pagination
    try:
        page     = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        raise BadRequest("page and per_page must be integers")

    start  = (page - 1) * per_page
    paged  = users[start : start + per_page]

    resp = jsonify({
        "users":    paged,
        "total":    len(users),
        "page":     page,
        "per_page": per_page,
    })
    resp.headers["X-Total-Count"] = str(len(users))
    return resp


@app.get("/api/users/<int:uid>")
def get_user(request, uid):
    """GET /api/users/1"""
    user = _users.get(uid)
    if not user:
        raise NotFound("User %d not found" % uid)
    return jsonify(user)


@app.post("/api/users")
def create_user(request):
    """
    POST /api/users
    Body: {"name": "...", "email": "...", "role": "user"}
    """
    global _next_id
    data = request.get_json()
    if not data:
        raise BadRequest("JSON body required")
    name  = data.get("name", "").strip()
    email = data.get("email", "").strip()
    role  = data.get("role", "user").strip()
    if not name:
        raise BadRequest("'name' is required")
    if not email or "@" not in email:
        raise BadRequest("Valid 'email' is required")

    uid = _next_id
    _next_id += 1
    _users[uid] = {"id": uid, "name": name, "email": email, "role": role}
    log.info("Created user #%d: %s" % (uid, name))
    return jsonify(_users[uid]), 201


@app.put("/api/users/<int:uid>")
def update_user(request, uid):
    """PUT /api/users/1  – full replace"""
    if uid not in _users:
        raise NotFound("User %d not found" % uid)
    data = request.get_json()
    if not data:
        raise BadRequest("JSON body required")
    _users[uid].update({
        "name":  data.get("name",  _users[uid]["name"]),
        "email": data.get("email", _users[uid]["email"]),
        "role":  data.get("role",  _users[uid]["role"]),
    })
    return jsonify(_users[uid])


@app.patch("/api/users/<int:uid>")
def patch_user(request, uid):
    """PATCH /api/users/1  – partial update"""
    if uid not in _users:
        raise NotFound("User %d not found" % uid)
    data = request.get_json(silent=True) or {}
    for key in ("name", "email", "role"):
        if key in data:
            _users[uid][key] = data[key]
    return jsonify(_users[uid])


@app.delete("/api/users/<int:uid>")
def delete_user(request, uid):
    """DELETE /api/users/1"""
    if uid not in _users:
        raise NotFound("User %d not found" % uid)
    deleted = _users.pop(uid)
    log.info("Deleted user #%d: %s" % (uid, deleted["name"]))
    return jsonify({"deleted": deleted}), 200


# ============================================================
# Form + Server-Side Rendering
# ============================================================

@app.get("/login")
def login_page(request):
    """Render HTML login form."""
    html = render_template("login.html", title="Login", error="")
    return html, 200, "text/html; charset=utf-8"


@app.post("/login")
def login_submit(request):
    """Handle login form POST."""
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if username == "admin" and password == "pico":
        resp = make_response()
        resp.set_cookie("session", "demo-token-12345", max_age=3600, httponly=True, samesite="Strict")
        resp.status = 302
        resp.headers["Location"] = "/dashboard"
        return resp
    else:
        html = render_template("login.html", title="Login", error="Invalid credentials")
        return html, 401, "text/html; charset=utf-8"


@app.get("/dashboard")
def dashboard(request):
    """Protected dashboard – requires session cookie."""
    session = request.cookies.get("session")
    if not session:
        return redirect("/login")

    html = render_template("dashboard.html",
        title    = "Dashboard",
        username = "admin",
        users    = list(_users.values()),
        mem_free = __import__("gc").mem_free(),
    )
    return html, 200, "text/html; charset=utf-8"


@app.get("/logout")
def logout(request):
    resp = make_response()
    resp.delete_cookie("session")
    resp.status = 302
    resp.headers["Location"] = "/login"
    return resp


# ============================================================
# Blueprint example  –  /api/v2/sensor
# ============================================================

sensor_bp = Blueprint("sensor", url_prefix="/api/v2")

_sensor_data = []

@sensor_bp.post("/sensor")
def post_sensor(request):
    """POST /api/v2/sensor  – receive a sensor reading."""
    data = request.get_json()
    if not data:
        raise BadRequest("JSON body required")
    reading = {
        "ts":          time.time(),
        "temperature": data.get("temperature"),
        "humidity":    data.get("humidity"),
        "pressure":    data.get("pressure"),
    }
    _sensor_data.append(reading)
    # Keep last 100 readings only (Pico W RAM is limited)
    if len(_sensor_data) > 100:
        _sensor_data.pop(0)
    return jsonify(reading), 201


@sensor_bp.get("/sensor")
def get_sensor(request):
    """GET /api/v2/sensor?n=10  – retrieve last n readings."""
    try:
        n = int(request.args.get("n", 10))
    except ValueError:
        raise BadRequest("n must be an integer")
    return jsonify({
        "count":    len(_sensor_data),
        "readings": _sensor_data[-n:],
    })


@sensor_bp.get("/sensor/latest")
def get_latest_sensor(request):
    """GET /api/v2/sensor/latest  – most recent reading."""
    if not _sensor_data:
        return jsonify({"error": "No data yet"}), 404
    return jsonify(_sensor_data[-1])


# Blueprint-scoped before_request
@sensor_bp.before_request
def check_sensor_key(request):
    """Require X-Sensor-Key header for all sensor endpoints."""
    if request.headers.get("x-sensor-key") != "pico-secret":
        raise Unauthorized("X-Sensor-Key header required")


app.register_blueprint(sensor_bp)


# ============================================================
# Echo / debug endpoint  (disable in production)
# ============================================================

@app.route("/echo", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def echo(request):
    """Echo back request metadata – useful for debugging."""
    if not app.debug:
        raise Forbidden("Echo endpoint is disabled in production mode")
    return jsonify({
        "method":       request.method,
        "path":         request.path,
        "query":        request.args.to_dict(),
        "headers":      dict(request.headers),
        "content_type": request.content_type,
        "is_json":      request.is_json,
        "form":         request.form.to_dict(),
        "json":         request.json,
        "cookies":      request.cookies,
        "remote_addr":  request.remote_addr,
    })


# ============================================================
# Entry point
# ============================================================

def main():
    connect_wifi()
    app.run()

main()
