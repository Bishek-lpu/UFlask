# Error Handling

uFlask gives you fine-grained control over how errors are displayed — from built-in HTTP exceptions to custom application errors.

---

## How Errors Work

When an exception is raised inside a view function (or middleware), uFlask:

1. Checks for a **registered error handler** (most specific first)
2. Falls back to a **built-in JSON error response**
3. In `debug=True` mode, shows a **styled HTML traceback page**

---

## `abort()` — Raise HTTP Errors

The `abort()` function raises an `HTTPException` immediately, stopping the current request:

```python
from uflask import abort

@app.get("/users/<int:uid>")
def get_user(request, uid):
    user = db.get(uid)
    if not user:
        abort(404)                     # minimal
        abort(404, "User not found")   # with message
    return jsonify(user)
```

`abort()` can be called from anywhere — views, middleware, helper functions.

---

## Named Exception Classes

Import and raise these instead of numeric codes for self-documenting code:

```python
from uflask import (
    BadRequest,          # 400
    Unauthorized,        # 401
    Forbidden,           # 403
    NotFound,            # 404
    MethodNotAllowed,    # 405
    Conflict,            # 409
    Gone,                # 410
    PayloadTooLarge,     # 413
    UnsupportedMediaType,# 415
    UnprocessableEntity, # 422
    TooManyRequests,     # 429
    InternalServerError, # 500
    ServiceUnavailable,  # 503
)

@app.post("/items")
def create_item(request):
    if not request.is_json:
        raise UnsupportedMediaType("Send JSON please")

    data = request.get_json()
    if not data.get("name"):
        raise BadRequest("'name' field is required")

    if item_exists(data["name"]):
        raise Conflict("An item with that name already exists")

    return jsonify(create(data)), 201
```

### `TooManyRequests` with `Retry-After`

```python
raise TooManyRequests("Slow down!", retry_after=60)
# → 429 response with  Retry-After: 60
```

### `ServiceUnavailable` with `Retry-After`

```python
raise ServiceUnavailable("DB offline", retry_after=30)
# → 503 response with  Retry-After: 30
```

---

## `@app.errorhandler()` — Custom Error Handlers

### By HTTP status code

```python
@app.errorhandler(404)
def not_found(exc):
    return jsonify({
        "error":   "Not found",
        "detail":  str(exc),
        "status":  404,
    }), 404

@app.errorhandler(400)
def bad_request(exc):
    return jsonify({"error": str(exc)}), 400

@app.errorhandler(500)
def server_error(exc):
    from uflask import logging
    logging.exception("Server error", exc)
    return jsonify({"error": "Something went wrong"}), 500
```

### By exception type

```python
@app.errorhandler(ValueError)
def handle_value_error(exc):
    return jsonify({"error": "Validation failed", "detail": str(exc)}), 400

@app.errorhandler(TypeError)
def handle_type_error(exc):
    return jsonify({"error": "Type mismatch", "detail": str(exc)}), 400

class InsufficientFundsError(Exception):
    pass

@app.errorhandler(InsufficientFundsError)
def handle_funds_error(exc):
    return jsonify({"error": "Insufficient funds"}), 402
```

### Handler resolution order

1. Exact exception class
2. Walk the MRO (parent classes)
3. HTTP status code (for `HTTPException` subclasses)
4. Catch-all `500` handler

---

## Default Error Responses

Without a custom handler, errors return JSON:

```json
{
    "error": "Not Found",
    "status": 404
}
```

---

## Debug Mode — HTML Tracebacks

Enable `debug=True` to get a styled HTML page with the full Python traceback on every error:

```python
app = UFlask(__name__, debug=True)
```

The debug error page shows:
- Status code badge
- Exception type and message
- Full Python traceback
- Request method, path, and headers
- Server version

> **Never use `debug=True` in production.** It exposes internal code and variable values.

---

## Production Error Page Pattern

```python
app = UFlask(__name__, debug=False)  # debug OFF in production

@app.errorhandler(400)
def bad_request(exc):
    return jsonify({"error": "Bad request", "hint": str(exc)}), 400

@app.errorhandler(401)
def unauthorized(exc):
    return jsonify({"error": "Authentication required"}), 401

@app.errorhandler(403)
def forbidden(exc):
    return jsonify({"error": "Access denied"}), 403

@app.errorhandler(404)
def not_found(exc):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(405)
def method_not_allowed(exc):
    return jsonify({"error": str(exc)}), 405

@app.errorhandler(422)
def unprocessable(exc):
    return jsonify({"error": "Validation failed", "detail": str(exc)}), 422

@app.errorhandler(429)
def rate_limited(exc):
    return jsonify({"error": "Too many requests", "retry_after": 60}), 429

@app.errorhandler(500)
def server_error(exc):
    # Log the error (never expose internals to the client)
    from uflask import logging
    logging.exception("Unhandled error", exc)
    return jsonify({"error": "Internal server error"}), 500
```

---

## Raising Errors from Middleware

```python
@app.before_request
def check_body_size(request):
    if request.content_length > 65536:
        raise PayloadTooLarge("Request body too large (max 64 kB)")

@app.before_request
def enforce_https(request):
    if not request.is_secure and request.path.startswith("/api/"):
        raise Forbidden("HTTPS required for API calls")
```

---

## `HTTPException` Base Class

All named exceptions inherit from `HTTPException`. You can catch it in your handlers to cover all HTTP errors at once:

```python
@app.errorhandler(HTTPException)
def handle_http_error(exc):
    return jsonify({
        "error":  exc.description,
        "status": exc.status,
    }), exc.status
```

---

## Exception Reference

| Class | Code | Description |
|---|---|---|
| `BadRequest` | 400 | Invalid input / missing field |
| `Unauthorized` | 401 | Authentication required |
| `Forbidden` | 403 | Access denied |
| `NotFound` | 404 | Resource not found |
| `MethodNotAllowed` | 405 | Wrong HTTP method |
| `Conflict` | 409 | Duplicate / state conflict |
| `Gone` | 410 | Resource permanently removed |
| `PayloadTooLarge` | 413 | Body exceeds size limit |
| `UnsupportedMediaType` | 415 | Wrong Content-Type |
| `UnprocessableEntity` | 422 | Validation failed |
| `TooManyRequests` | 429 | Rate limit exceeded |
| `InternalServerError` | 500 | Unexpected server error |
| `ServiceUnavailable` | 503 | Maintenance / overload |
