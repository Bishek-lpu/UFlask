# uflask/response.py
# Full-featured HTTP response objects for MicroPython (Raspberry Pi Pico W)
# Mirrors Flask's Response / helper API.

import json as _json
import os as _os


# ---------------------------------------------------------------------------
# HTTP status code registry
# ---------------------------------------------------------------------------

STATUS = {
    100: "Continue",
    101: "Switching Protocols",
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    206: "Partial Content",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    413: "Payload Too Large",
    414: "URI Too Long",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}

# ---------------------------------------------------------------------------
# MIME type map (by file extension)
# ---------------------------------------------------------------------------

MIME = {
    "html":  "text/html; charset=utf-8",
    "htm":   "text/html; charset=utf-8",
    "txt":   "text/plain; charset=utf-8",
    "css":   "text/css",
    "js":    "application/javascript",
    "mjs":   "application/javascript",
    "json":  "application/json",
    "png":   "image/png",
    "jpg":   "image/jpeg",
    "jpeg":  "image/jpeg",
    "gif":   "image/gif",
    "svg":   "image/svg+xml",
    "ico":   "image/x-icon",
    "xml":   "application/xml",
    "pdf":   "application/pdf",
    "woff":  "font/woff",
    "woff2": "font/woff2",
    "ttf":   "font/ttf",
    "otf":   "font/otf",
    "mp3":   "audio/mpeg",
    "wav":   "audio/wav",
    "mp4":   "video/mp4",
    "webm":  "video/webm",
    "gz":    "application/gzip",
    "zip":   "application/zip",
    "bin":   "application/octet-stream",
}


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class Response:
    """
    HTTP response object.

    Parameters
    ----------
    body         : str | bytes | None  – response body
    status       : int                 – HTTP status code (default 200)
    headers      : dict | None         – extra response headers
    content_type : str | None          – overrides Content-Type header
    """

    def __init__(self, body="", status=200, headers=None, content_type=None):
        self.body    = body
        self.status  = int(status)
        self.headers = dict(headers or {})

        if content_type:
            self.headers["Content-Type"] = content_type
        elif "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "text/html; charset=utf-8"

    # ------------------------------------------------------------------
    # Convenience setters (chainable, Flask-style)
    # ------------------------------------------------------------------

    def set_cookie(
        self,
        key,
        value="",
        max_age=None,
        expires=None,
        path="/",
        domain=None,
        secure=False,
        httponly=False,
        samesite="Lax",
    ):
        """
        Add a Set-Cookie header.

        Parameters match Flask's response.set_cookie() signature.
        Returns *self* so calls can be chained.
        """
        cookie = "%s=%s" % (key, value)
        if path:
            cookie += "; Path=%s" % path
        if domain:
            cookie += "; Domain=%s" % domain
        if max_age is not None:
            cookie += "; Max-Age=%d" % int(max_age)
        if expires is not None:
            cookie += "; Expires=%s" % expires
        if secure:
            cookie += "; Secure"
        if httponly:
            cookie += "; HttpOnly"
        if samesite:
            cookie += "; SameSite=%s" % samesite

        # Allow multiple Set-Cookie headers by using a list internally
        existing = self.headers.get("Set-Cookie")
        if existing is None:
            self.headers["Set-Cookie"] = cookie
        elif isinstance(existing, list):
            existing.append(cookie)
        else:
            self.headers["Set-Cookie"] = [existing, cookie]
        return self

    def delete_cookie(self, key, path="/", domain=None):
        """Expire a cookie immediately. Returns *self*."""
        return self.set_cookie(key, "", max_age=0, expires="Thu, 01 Jan 1970 00:00:00 GMT",
                               path=path, domain=domain)

    def set_header(self, key, value):
        """Set a single response header. Returns *self*."""
        self.headers[key] = value
        return self

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    @property
    def status_line(self):
        return "%d %s" % (self.status, STATUS.get(self.status, "Unknown"))

    def __repr__(self):
        return "<Response %s>" % self.status_line


# ---------------------------------------------------------------------------
# FileResponse  –  streams a file from the filesystem
# ---------------------------------------------------------------------------

class FileResponse(Response):
    """
    Stream a file to the client.

    Sets Content-Type from the file extension, Content-Length from stat,
    and falls back to 404 if the file cannot be found.
    """

    def __init__(self, filename, status=200, headers=None, download_name=None):
        self.filename      = filename
        self.download_name = download_name
        self.status        = int(status)
        self.headers       = dict(headers or {})
        self.body          = None   # sent by _send in app.py

        try:
            stat = _os.stat(filename)
            size = stat[6]
            ext  = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

            self.headers["Content-Length"] = str(size)
            self.headers.setdefault("Content-Type", MIME.get(ext, "application/octet-stream"))

            if download_name:
                self.headers["Content-Disposition"] = (
                    'attachment; filename="%s"' % download_name
                )
        except OSError:
            self.status = 404
            self.headers["Content-Type"] = "text/plain; charset=utf-8"


# ---------------------------------------------------------------------------
# Helper factory functions  (mirrors Flask's top-level helpers)
# ---------------------------------------------------------------------------

def jsonify(data, status=200, headers=None, indent=None):
    """
    Serialize *data* to JSON and return a Response with
    Content-Type: application/json.

    Usage::

        return jsonify({"ok": True})
        return jsonify(users, status=201)
    """
    h = dict(headers or {})
    h["Content-Type"] = "application/json"
    body = _json.dumps(data) if indent is None else _json.dumps(data)
    return Response(body, status, h)


def redirect(location, status=302):
    """
    Return an HTTP redirect response.

    Usage::

        return redirect("/login")
        return redirect("https://example.com", 301)
    """
    return Response(
        "",
        int(status),
        {"Location": location, "Content-Length": "0"},
    )


def send_file(filename, headers=None, download_name=None):
    """
    Return a FileResponse for the given filesystem path.

    Usage::

        return send_file("/static/data.csv", download_name="export.csv")
    """
    return FileResponse(filename, headers=headers, download_name=download_name)


def abort(status, description=None):
    """
    Raise an HTTPException with the given status code.

    Usage::

        abort(404)
        abort(403, "You shall not pass")
    """
    from .exceptions import HTTPException
    raise HTTPException(status, description)


def make_response(body="", status=200, headers=None, content_type=None):
    """
    Create a Response explicitly (like Flask's make_response).

    Usage::

        resp = make_response("hello", 200)
        resp.set_cookie("session", token)
        return resp
    """
    return Response(body, status, headers, content_type)
