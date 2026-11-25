# uflask/app.py
# Core UFlask application engine for MicroPython / Raspberry Pi Pico W.
# Mirrors Flask's application class API as closely as the hardware allows.
#
# Features
# --------
#  • Async HTTP/1.1 server via uasyncio
#  • Route registration:  @app.route / .get / .post / .put / .patch / .delete / .options / .head
#  • URL parameters:      /users/<id>  /files/<path:name>
#  • Before / after / teardown request hooks
#  • before_first_request hook
#  • Middleware stack
#  • Blueprint registration
#  • CORS integration
#  • Custom error handlers:  @app.errorhandler(404)
#  • debug=True → pretty HTML error pages + stack traces
#  • Static file serving:    /static/<filename>
#  • Multipart body parsing (small files only, Pico W RAM limit)
#  • Configurable max body size
#  • Graceful keep-alive / connection: close
#  • GC collect between requests
#  • Structured logging

import sys

from ._compat import asyncio, gc, os, time   # noqa: F401 – platform shim

from .request  import Request, _parse_multidict, _parse_multipart, parse_query_string
from .response import Response, FileResponse, STATUS, jsonify, make_response
from .exceptions import HTTPException, ErrorHandlerRegistry, MethodNotAllowed, NotFound, InternalServerError
from .middleware import MiddlewareStack
from . import logging as _log


# ---------------------------------------------------------------------------
# _Route
# ---------------------------------------------------------------------------

class _Route:
    """
    Compiled URL rule.

    Segments of the form ``<name>`` are variable; ``<path:name>`` captures
    the rest of the URL including slashes.
    """

    def __init__(self, path, handler, methods):
        self.path     = path
        self.handler  = handler
        self.methods  = [m.upper() for m in methods]
        self._parts   = self._compile(path)

    @staticmethod
    def _compile(path):
        """Return list of ('literal', value) | ('var', name) | ('path', name)."""
        parts = []
        for seg in path.strip("/").split("/"):
            if not seg:
                continue
            if seg.startswith("<") and seg.endswith(">"):
                inner = seg[1:-1]
                if inner.startswith("path:"):
                    parts.append(("path", inner[5:]))
                elif inner.startswith("int:"):
                    parts.append(("int",  inner[4:]))
                elif inner.startswith("float:"):
                    parts.append(("float", inner[6:]))
                else:
                    parts.append(("var", inner))
            else:
                parts.append(("literal", seg))
        return parts

    def match(self, request):
        """
        Try to match *request* against this rule.
        Returns a dict of path variables on success, None on failure.
        """
        if request.method not in self.methods:
            return None

        path_segs = [s for s in request.path.strip("/").split("/") if s or request.path == "/"]
        if request.path == "/":
            path_segs = []

        values = {}
        pi     = 0   # index into path_segs
        ri     = 0   # index into self._parts

        while ri < len(self._parts):
            kind, name = self._parts[ri]
            ri += 1

            if kind == "literal":
                if pi >= len(path_segs) or path_segs[pi] != name:
                    return None
                pi += 1

            elif kind == "path":
                # Consume the rest of path_segs
                values[name] = "/".join(path_segs[pi:])
                pi = len(path_segs)

            elif kind == "int":
                if pi >= len(path_segs):
                    return None
                try:
                    values[name] = int(path_segs[pi])
                except ValueError:
                    return None
                pi += 1

            elif kind == "float":
                if pi >= len(path_segs):
                    return None
                try:
                    values[name] = float(path_segs[pi])
                except ValueError:
                    return None
                pi += 1

            else:  # "var"
                if pi >= len(path_segs):
                    return None
                values[name] = path_segs[pi]
                pi += 1

        # All rule parts consumed; path must also be fully consumed
        # (unless the last rule part was a <path:…> catcher)
        if pi != len(path_segs):
            return None

        return values


# ---------------------------------------------------------------------------
# UFlask application
# ---------------------------------------------------------------------------

class UFlask:
    """
    MicroPython web application – mirrors Flask's public API.

    Parameters
    ----------
    name         : str   – application name (use __name__)
    host         : str   – bind address   (default "0.0.0.0")
    port         : int   – TCP port       (default 80)
    debug        : bool  – enable debug mode (pretty error pages, verbose logging)
    static_dir   : str   – filesystem directory for static files (default "static")
    static_url   : str   – URL prefix for static files (default "/static")
    max_body_size: int   – maximum request body in bytes (default 8192)
    backlog      : int   – TCP listen backlog (default 5)
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        name        = "uflask",
        host        = "0.0.0.0",
        port        = 80,
        debug       = False,
        static_dir  = "static",
        static_url  = "/static",
        max_body_size = 8192,
        backlog     = 5,
    ):
        self.name          = name
        self.host          = host
        self.port          = int(port)
        self.debug         = debug
        self.static_dir    = static_dir.rstrip("/")
        self.static_url    = static_url.rstrip("/")
        self.max_body_size = int(max_body_size)
        self.backlog       = int(backlog)

        self._routes     = []
        self.middleware  = MiddlewareStack()
        self._errors     = ErrorHandlerRegistry()
        self.cors        = None             # set by CORS(app, ...)
        self.config      = {}              # arbitrary key/value config store

        # Logging level
        if debug:
            _log.set_level(_log.DEBUG)
        else:
            _log.set_level(_log.INFO)

        # Register built-in static file route
        if static_dir and static_url:
            self._add_route(
                self.static_url + "/<path:filename>",
                self._static_handler,
                ["GET", "HEAD"],
            )

    # ==================================================================
    # Route registration
    # ==================================================================

    def _add_route(self, path, handler, methods):
        self._routes.append(_Route(path, handler, methods))

    def route(self, path, methods=None):
        """
        Decorator to register a route handler.

        @app.route("/users/<int:uid>", methods=["GET", "POST"])
        def user(request, uid):
            ...
        """
        if methods is None:
            methods = ["GET"]
        if isinstance(methods, str):
            methods = [methods]

        def decorator(fn):
            self._add_route(path, fn, methods)
            return fn
        return decorator

    def get(self, path):
        return self.route(path, ["GET"])

    def post(self, path):
        return self.route(path, ["POST"])

    def put(self, path):
        return self.route(path, ["PUT"])

    def patch(self, path):
        return self.route(path, ["PATCH"])

    def delete(self, path):
        return self.route(path, ["DELETE"])

    def options(self, path):
        return self.route(path, ["OPTIONS"])

    def head(self, path):
        return self.route(path, ["HEAD"])

    # ------------------------------------------------------------------
    # Hook decorators  (Flask-style)
    # ------------------------------------------------------------------

    def before_request(self, fn):
        """Register a before_request hook."""
        self.middleware.add_before(fn)
        return fn

    def after_request(self, fn):
        """Register an after_request hook."""
        self.middleware.add_after(fn)
        return fn

    def teardown_request(self, fn):
        """Register a teardown_request hook."""
        self.middleware.add_teardown(fn)
        return fn

    def before_first_request(self, fn):
        """Register a hook called only before the very first request."""
        self.middleware.add_before_first(fn)
        return fn

    # ------------------------------------------------------------------
    # Error handler decorator
    # ------------------------------------------------------------------

    def errorhandler(self, code_or_exc):
        """
        Register a custom error handler.

        @app.errorhandler(404)
        def not_found(exc):
            return jsonify({"error": str(exc)}), 404

        @app.errorhandler(ValueError)
        def handle_value_error(exc):
            return jsonify({"error": str(exc)}), 400
        """
        def decorator(fn):
            self._errors.register(code_or_exc, fn)
            return fn
        return decorator

    # ------------------------------------------------------------------
    # Blueprint registration
    # ------------------------------------------------------------------

    def register_blueprint(self, bp):
        """
        Attach a Blueprint's routes and hooks to this app.

        app.register_blueprint(auth_bp)
        """
        bp._register(self)
        _log.info("Blueprint '%s' registered (prefix=%r, routes=%d)" % (
            bp.name, bp.url_prefix, len(bp._routes)
        ))

    # ==================================================================
    # Internal – routing
    # ==================================================================

    def _match(self, request):
        """
        Return (route, params) for the best matching route, or
        raise MethodNotAllowed / NotFound appropriately.
        """
        allowed = []
        for route in self._routes:
            # Try without method constraint first to find allowed methods
            if request.path.strip("/").split("/") or request.path == "/":
                # Test path match ignoring method
                temp_method = request.method
                request.method = route.methods[0]  # set a known-good method temporarily
                params = route.match(request)
                request.method = temp_method
                if params is not None:
                    allowed.extend(m for m in route.methods if m not in allowed)

            # Now test with the actual method
            params = route.match(request)
            if params is not None:
                return route, params

        if allowed:
            raise MethodNotAllowed(allowed)
        raise NotFound()

    # ==================================================================
    # Internal – body reading
    # ==================================================================

    async def _read_body(self, reader, request):
        length = request.content_length
        if length <= 0:
            return
        if length > self.max_body_size:
            from .exceptions import PayloadTooLarge
            raise PayloadTooLarge(
                "Body %d bytes exceeds max %d bytes" % (length, self.max_body_size)
            )

        request.data = await reader.readexactly(length)
        ctype = request.content_type

        if "application/json" in ctype:
            import json
            try:
                request.json = json.loads(request.data.decode())
            except Exception as e:
                if self.debug:
                    raise
                request.json = None

        elif "application/x-www-form-urlencoded" in ctype:
            request.form = _parse_multidict(request.data.decode())

        elif "multipart/form-data" in ctype:
            # Extract boundary
            boundary = ""
            for part in ctype.split(";"):
                part = part.strip()
                if part.startswith("boundary="):
                    boundary = part[9:].strip().strip('"')
                    break
            if boundary:
                fields, files = _parse_multipart(request.data, boundary)
                for k, v in fields.items():
                    request.form.add(k, v)
                request.files = files

    # ==================================================================
    # Internal – static file handler
    # ==================================================================

    def _static_handler(self, request, filename=""):
        import os
        # Basic path traversal protection
        if ".." in filename:
            from .exceptions import Forbidden
            raise Forbidden("Path traversal not allowed")
        path = self.static_dir + "/" + filename
        return FileResponse(path)

    # ==================================================================
    # Internal – response normalisation
    # ==================================================================

    def _normalize(self, result):
        """Convert any handler return value to a Response object."""
        if isinstance(result, (Response, FileResponse)):
            return result

        if isinstance(result, tuple):
            # (body,) or (body, status) or (body, status, headers/content_type)
            body    = result[0]
            status  = int(result[1]) if len(result) > 1 else 200
            extra   = result[2] if len(result) > 2 else None

            if isinstance(extra, dict):
                return Response(body, status, extra)
            elif isinstance(extra, str):
                return Response(body, status, content_type=extra)
            return Response(body, status)

        if result is None:
            return Response("", 204)

        if isinstance(result, (dict, list)):
            # Auto-JSON for plain dict/list returns
            import json
            return Response(
                json.dumps(result), 200,
                content_type="application/json",
            )

        return Response(str(result), 200, content_type="text/html; charset=utf-8")

    # ==================================================================
    # Internal – error response building
    # ==================================================================

    def _build_error_response(self, exc, request=None):
        """
        Build a Response for *exc*, preferring registered error handlers,
        then falling back to a formatted HTML/JSON error page.
        """
        handler = self._errors.find(exc)
        if handler is not None:
            try:
                result = handler(exc)
                return self._normalize(result)
            except Exception as inner:
                _log.error("Error inside error handler:", inner)

        # No handler found – build a default response
        if isinstance(exc, HTTPException):
            status = exc.status
            msg    = exc.description
        else:
            status = 500
            msg    = str(exc)

        if self.debug:
            return self._debug_error_page(exc, status, request)

        # Production – plain JSON error
        import json
        body = json.dumps({"error": msg, "status": status})
        return Response(body, status, content_type="application/json")

    def _debug_error_page(self, exc, status, request=None):
        """Return a styled HTML error page with traceback (debug mode only)."""
        import io
        buf = io.StringIO()
        sys.print_exception(exc, buf)
        tb = buf.getvalue()

        req_info = ""
        if request:
            req_info = (
                "<p><b>Request:</b> %s %s</p>"
                "<p><b>Headers:</b> %s</p>"
            ) % (request.method, request.path, str(request.headers))

        html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>uFlask Error %d</title>
  <style>
    body{{font-family:monospace;background:#1e1e1e;color:#d4d4d4;padding:2rem}}
    h1{{color:#f44747}}
    pre{{background:#252526;padding:1rem;border-radius:4px;overflow-x:auto;white-space:pre-wrap}}
    .badge{{display:inline-block;padding:.2rem .6rem;border-radius:3px;
            background:#f44747;color:#fff;font-size:.85rem;margin-bottom:1rem}}
    .info{{color:#9cdcfe}}
  </style>
</head>
<body>
  <span class="badge">%d %s</span>
  <h1>%s: %s</h1>
  %s
  <h2>Traceback</h2>
  <pre>%s</pre>
  <p style="color:#555">uFlask %s – debug mode</p>
</body>
</html>""" % (
            status,
            status, STATUS.get(status, "Error"),
            type(exc).__name__, str(exc),
            req_info,
            tb,
            self.VERSION,
        )
        return Response(html, status, content_type="text/html; charset=utf-8")

    # ==================================================================
    # Internal – request/response cycle
    # ==================================================================

    async def _handle(self, reader, writer):
        """Main connection handler – one call per TCP connection."""
        started = time.ticks_ms()
        request = None
        exc_ctx = None

        try:
            gc.collect()

            # ---- Parse request line ----
            line = await asyncio.wait_for(reader.readline(), timeout=10)
            if not line or line == b"\r\n":
                return

            try:
                parts = line.decode().strip().split()
                if len(parts) < 2:
                    return
                method   = parts[0]
                uri      = parts[1]
                protocol = parts[2] if len(parts) > 2 else "HTTP/1.0"
            except Exception:
                return

            # ---- Parse headers ----
            headers = {}
            while True:
                line = await asyncio.wait_for(reader.readline(), timeout=5)
                if not line or line == b"\r\n":
                    break
                try:
                    decoded = line.decode().strip()
                    if ":" in decoded:
                        key, _, value = decoded.partition(":")
                        headers[key.lower().strip()] = value.strip()
                except Exception:
                    continue

            # Peer address (best-effort)
            try:
                remote_addr = writer.get_extra_info("peername")[0]
            except Exception:
                remote_addr = None

            request = Request(method, uri, protocol, headers, remote_addr)

            # ---- Before first request ----
            await self.middleware.run_before_first()

            # ---- Handle CORS preflight ----
            if method.upper() == "OPTIONS" and self.cors is not None:
                preflight_resp = self.cors.preflight(request)
                if preflight_resp is not None:
                    await self._send(writer, preflight_resp)
                    return

            # ---- Read body ----
            await self._read_body(reader, request)

            # ---- Before request hooks ----
            early = await self.middleware.run_before(request)
            if early is not None:
                response = self._normalize(early)
            else:
                # ---- Route matching ----
                route, params = self._match(request)
                request.endpoint  = getattr(route.handler, "__name__", "unknown")
                request.view_args = params

                # ---- Call handler ----
                result = route.handler(request, **params)
                if hasattr(result, "__await__"):
                    result = await result
                response = self._normalize(result)

            # ---- After request hooks ----
            response = await self.middleware.run_after(request, response)

        except HTTPException as exc:
            exc_ctx  = exc
            response = self._build_error_response(exc, request)

        except TimeoutError as exc:
            # asyncio.wait_for() raised TimeoutError — MicroPython's TimeoutError
            # does not have __mro__, so handle it here before it reaches
            # _build_error_response / ErrorHandlerRegistry.
            exc_ctx = exc
            _log.warning("Request timed out")
            response = Response(
                "408 Request Timeout",
                408,
                content_type="text/plain; charset=utf-8",
            )

        except OSError as exc:
            # Client disconnected mid-request — not an application error
            exc_ctx = exc
            _log.debug("OSError during request (client disconnect?): %s" % exc)
            return

        except Exception as exc:
            exc_ctx = exc
            _log.exception("Unhandled exception during request", exc)
            try:
                response = self._build_error_response(exc, request)
            except Exception as inner:
                _log.error("Error in _build_error_response: %s" % inner)
                response = Response(
                    "500 Internal Server Error",
                    500,
                    content_type="text/plain; charset=utf-8",
                )

        # ---- Apply CORS headers to real response ----
        if self.cors is not None and request is not None:
            response = self.cors.apply(request, response)

        # ---- Send response ----
        try:
            await self._send(writer, response)
        except Exception as exc:
            _log.error("Error sending response:", exc)

        # ---- Access log ----
        if request is not None:
            elapsed = time.ticks_diff(time.ticks_ms(), started)
            _log.info(
                "%s %s %s -> %d [%dms] %s" % (
                    request.remote_addr or "-",
                    request.method,
                    request.path,
                    response.status,
                    elapsed,
                    request.user_agent[:40] if request.user_agent else "-",
                )
            )

        # ---- Teardown hooks ----
        if request is not None:
            await self.middleware.run_teardown(request, exc_ctx)

        # ---- Close connection ----
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    # ==================================================================
    # Internal – HTTP response writer
    # ==================================================================

    async def _send(self, writer, response):
        """Serialise *response* and write it to *writer*."""
        status_text = STATUS.get(response.status, "Unknown")
        writer.write(
            ("HTTP/1.1 %d %s\r\n" % (response.status, status_text)).encode()
        )

        headers = dict(response.headers)
        headers.setdefault("Server",     "uFlask/%s" % self.VERSION)
        headers.setdefault("Connection", "close")

        is_file = isinstance(response, FileResponse)

        if is_file and response.status == 200:
            # Content-Length already set by FileResponse.__init__
            pass
        else:
            body = response.body
            if isinstance(body, str):
                body = body.encode("utf-8")
            headers.setdefault("Content-Length", str(len(body or b"")))

        # Write headers (handle multi-value Set-Cookie)
        for key, value in headers.items():
            if isinstance(value, list):
                for v in value:
                    writer.write(("%s: %s\r\n" % (key, v)).encode())
            else:
                writer.write(("%s: %s\r\n" % (key, value)).encode())

        writer.write(b"\r\n")
        await writer.drain()

        # Write body
        if is_file:
            if response.status != 200:
                writer.write(("File not found: %s" % response.filename).encode())
                await writer.drain()
            else:
                try:
                    with open(response.filename, "rb") as f:
                        while True:
                            chunk = f.read(512)
                            if not chunk:
                                break
                            writer.write(chunk)
                            await writer.drain()
                except OSError as exc:
                    _log.error("Static file read error:", exc)
        else:
            body = response.body
            if isinstance(body, str):
                body = body.encode("utf-8")
            if body:
                writer.write(body)
                await writer.drain()

    # ==================================================================
    # Server lifecycle
    # ==================================================================

    async def serve(self):
        """Start the async TCP server."""
        _log.info(
            "uFlask %s | %s | %s:%d | debug=%s" % (
                self.VERSION, self.name, self.host, self.port, self.debug
            )
        )
        server = await asyncio.start_server(
            self._handle,
            self.host,
            self.port,
            backlog=self.backlog,
        )
        _log.info("Listening on http://%s:%d" % (self.host, self.port))
        # Keep the coroutine alive
        while True:
            await asyncio.sleep(3600)

    def run(self, host=None, port=None, debug=None):
        """
        Start the server (blocking call).

        Parameters override the constructor values when provided.

        Usage::

            app.run(host="0.0.0.0", port=80, debug=True)
        """
        if host  is not None: self.host  = host
        if port  is not None: self.port  = int(port)
        if debug is not None:
            self.debug = debug
            _log.set_level(_log.DEBUG if debug else _log.INFO)

        try:
            asyncio.run(self.serve())
        except KeyboardInterrupt:
            _log.info("Server stopped by KeyboardInterrupt")
        except Exception as exc:
            _log.exception("Fatal server error", exc)
            raise

    # ------------------------------------------------------------------
    # Flask-style context helpers
    # ------------------------------------------------------------------

    def url_for(self, endpoint, **values):
        """
        Build a URL for the given endpoint name.

        url_for("user_detail", uid=42)  →  "/users/42"

        Note: only literal + variable segments are supported (no host).
        """
        for route in self._routes:
            handler_name = getattr(route.handler, "__name__", "")
            bp_name      = getattr(route.handler, "_bp_name", None)
            qualified    = ("%s.%s" % (bp_name, handler_name)) if bp_name else handler_name
            if qualified == endpoint or handler_name == endpoint:
                return self._build_url(route, values)
        raise KeyError("No route for endpoint '%s'" % endpoint)

    @staticmethod
    def _build_url(route, values):
        parts = []
        for kind, name in route._parts:
            if kind == "literal":
                parts.append(name)
            elif kind in ("var", "int", "float", "path"):
                if name not in values:
                    raise KeyError("Missing URL variable '%s'" % name)
                parts.append(str(values.pop(name)))
        url = "/" + "/".join(parts)
        # Append remaining values as query string
        if values:
            qs = "&".join("%s=%s" % (k, v) for k, v in values.items())
            url += "?" + qs
        return url

    def __repr__(self):
        return "<UFlask %r %s:%d debug=%s>" % (
            self.name, self.host, self.port, self.debug
        )
