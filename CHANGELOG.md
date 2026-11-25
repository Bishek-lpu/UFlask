# Changelog

All notable changes to **uFlask** are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),  
versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] – 2026-11-25

### Added
- **`UFlask` application class** — async HTTP/1.1 server built on `uasyncio`
- **Route decorators** — `@app.get`, `@app.post`, `@app.put`, `@app.patch`,
  `@app.delete`, `@app.options`, `@app.head`, `@app.route(methods=[…])`
- **URL converters** — `<name>`, `<int:n>`, `<float:n>`, `<path:p>`
- **`Request` object** — `args`, `form`, `files`, `json`, `cookies`,
  `headers`, `remote_addr`, `is_json`, `is_secure`, `user_agent`,
  `get_json()`, `get_data()`, `values()`
- **`MultiDict`** — multi-value query/form dict with `.getlist()`
- **Multipart form-data parser** — file upload support
- **`Response`, `FileResponse`** — with `.set_cookie()`, `.delete_cookie()`,
  `.set_header()` chainable setters
- **Helper functions** — `jsonify()`, `redirect()`, `send_file()`,
  `make_response()`, `abort()`
- **`CORS`** — full preflight (OPTIONS), `Access-Control-*` headers,
  credentials support, `Vary: Origin`
- **`Blueprint`** — split app into modules with `url_prefix` and
  per-blueprint hooks
- **Middleware stack** — `@app.before_request`, `@app.after_request`,
  `@app.teardown_request`, `@app.before_first_request`
- **Custom error handlers** — `@app.errorhandler(404)`,
  `@app.errorhandler(ValueError)`
- **`HTTPException` hierarchy** — `BadRequest`, `Unauthorized`, `Forbidden`,
  `NotFound`, `MethodNotAllowed`, `Conflict`, `Gone`, `PayloadTooLarge`,
  `UnsupportedMediaType`, `UnprocessableEntity`, `TooManyRequests`,
  `InternalServerError`, `ServiceUnavailable`
- **`ErrorHandlerRegistry`** — resolves handlers by MRO then HTTP status code
- **Template engine** — `render_template()`, `render_string()`;
  Jinja2-compatible syntax: `{{ var }}`, `{% if %}`, `{% for %}`, `{% set %}`,
  `{# comments #}`, `loop.index / .first / .last`, `| raw` filter
- **Structured logger** — `DEBUG/INFO/WARNING/ERROR/CRITICAL` levels,
  optional file logging, ANSI colour, per-module `Logger` via `getLogger()`
- **Static file serving** — built-in `/static/<path:filename>` route
- **`debug=True` mode** — styled HTML error page with full traceback
- **`url_for()`** — reverse URL building from endpoint names
- **`app.config` dict** — arbitrary key/value configuration store
- **Security headers** — `X-Content-Type-Options`, `X-Frame-Options`
  added in example middleware
- **`py.typed` marker** — PEP 561 type-checked package
- Full CPython `pyproject.toml` + `setup.cfg` packaging
- MIT licence

---

## [0.1.0] – 2026-11-24  *(pre-release)*

### Added
- Initial prototype: `UFlask`, basic routing, `Request`, `Response`,
  `jsonify`, `redirect`, `CORS`, `render_template`, `logging`
