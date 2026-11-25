# uflask/request.py
# Full-featured HTTP request object for MicroPython (Raspberry Pi Pico W)
# Mirrors Flask's request API as closely as MicroPython allows.

import json as _json


# ---------------------------------------------------------------------------
# URL / query-string helpers
# ---------------------------------------------------------------------------

def _decode_percent(value):
    """URL-decode a percent-encoded string (handles %XX and + → space)."""
    value = value.replace("+", " ")
    out = bytearray()
    i = 0
    while i < len(value):
        if value[i] == "%" and i + 2 < len(value):
            try:
                out.append(int(value[i + 1 : i + 3], 16))
                i += 3
                continue
            except ValueError:
                pass
        try:
            out.extend(value[i].encode())
        except Exception:
            out.append(ord(value[i]))
        i += 1
    try:
        return out.decode()
    except Exception:
        return value


def parse_query_string(query):
    """Parse a URL-encoded query string into a plain dict."""
    result = {}
    if not query:
        return result
    for item in query.split("&"):
        if not item:
            continue
        key, sep, value = item.partition("=")
        result[_decode_percent(key)] = _decode_percent(value if sep else "")
    return result


# ---------------------------------------------------------------------------
# MultiDict – preserves multiple values for the same key (like Flask's ImmutableMultiDict)
# ---------------------------------------------------------------------------

class MultiDict(dict):
    """dict subclass that keeps lists under each key; .get() returns last value."""

    def __init__(self):
        super().__init__()
        self._lists = {}

    def add(self, key, value):
        self._lists.setdefault(key, []).append(value)
        self[key] = value          # dict key → last value (Flask behaviour)

    def getlist(self, key, default=None):
        """Return all values for *key* as a list."""
        return self._lists.get(key, default if default is not None else [])

    def to_dict(self):
        return dict(self)


def _parse_multidict(query):
    """Return a MultiDict parsed from a URL-encoded string."""
    md = MultiDict()
    if not query:
        return md
    for item in query.split("&"):
        if not item:
            continue
        key, sep, value = item.partition("=")
        md.add(_decode_percent(key), _decode_percent(value if sep else ""))
    return md


# ---------------------------------------------------------------------------
# Cookie parsing
# ---------------------------------------------------------------------------

def parse_cookies(cookie_header):
    """Parse a Cookie: header into a plain dict."""
    cookies = {}
    if not cookie_header:
        return cookies
    for part in cookie_header.split(";"):
        key, sep, value = part.strip().partition("=")
        if key:
            cookies[key.strip()] = value.strip()
    return cookies


# ---------------------------------------------------------------------------
# Multipart form-data parser (simple, single-file friendly for Pico W RAM)
# ---------------------------------------------------------------------------

def _parse_multipart(data, boundary):
    """
    Very lightweight multipart/form-data parser.
    Returns (fields_dict, files_dict).
    files_dict values are dicts: {filename, content_type, data}.
    """
    fields = {}
    files  = {}

    if isinstance(data, str):
        data = data.encode()

    delimiter = b"--" + boundary.encode()
    parts = data.split(delimiter)

    for part in parts[1:]:
        if part in (b"--\r\n", b"--", b""):
            continue
        # Strip leading \r\n
        if part.startswith(b"\r\n"):
            part = part[2:]
        # Separate headers from body
        sep = part.find(b"\r\n\r\n")
        if sep < 0:
            continue
        raw_headers = part[:sep].decode("utf-8", "ignore")
        body = part[sep + 4 :]
        if body.endswith(b"\r\n"):
            body = body[:-2]

        # Parse Content-Disposition
        disp = {}
        content_type = "text/plain"
        for hline in raw_headers.split("\r\n"):
            hname, _, hval = hline.partition(":")
            hname = hname.strip().lower()
            hval  = hval.strip()
            if hname == "content-disposition":
                for token in hval.split(";"):
                    token = token.strip()
                    k, eq, v = token.partition("=")
                    if eq:
                        disp[k.strip()] = v.strip().strip('"')
            elif hname == "content-type":
                content_type = hval

        fname = disp.get("name", "")
        if "filename" in disp:
            files[fname] = {
                "filename":     disp["filename"],
                "content_type": content_type,
                "data":         body,
            }
        else:
            try:
                fields[fname] = body.decode()
            except Exception:
                fields[fname] = body

    return fields, files


# ---------------------------------------------------------------------------
# Request class
# ---------------------------------------------------------------------------

class Request:
    """
    Mirrors Flask's request object.

    Attributes
    ----------
    method          : str            – HTTP method (GET, POST …)
    path            : str            – URL path  (/api/users)
    full_path       : str            – path + query string
    url             : str            – scheme://host + full_path
    uri             : str            – raw URI from the request line
    protocol        : str            – HTTP/1.0 or HTTP/1.1
    headers         : dict           – lower-cased header names
    args            : MultiDict      – query-string parameters
    form            : MultiDict      – form fields (URL-encoded / multipart)
    files           : dict           – uploaded files (multipart only)
    json            : any            – parsed JSON body (or None)
    data            : bytes          – raw request body
    cookies         : dict           – parsed Cookie header
    remote_addr     : str | None     – client IP
    content_type    : str            – Content-Type header value
    content_length  : int            – body length in bytes
    is_json         : bool           – True when Content-Type is application/json
    is_secure       : bool           – True when X-Forwarded-Proto is https
    endpoint        : str | None     – matched route handler name
    view_args       : dict           – URL path parameters
    """

    __slots__ = (
        "method", "uri", "protocol", "headers",
        "path", "query_string", "full_path",
        "args", "form", "files",
        "json", "data", "cookies",
        "remote_addr", "endpoint", "view_args",
        "_url",
    )

    def __init__(self, method, uri, protocol, headers=None, remote_addr=None):
        self.method      = method.upper()
        self.uri         = uri
        self.protocol    = protocol
        self.headers     = headers or {}
        self.remote_addr = remote_addr
        self.endpoint    = None
        self.view_args   = {}

        # Split URI → path + query
        self.path, _, self.query_string = uri.partition("?")
        self.full_path   = uri
        self._url        = None     # lazy

        # Parsed fields (populated after body is read)
        self.args  = _parse_multidict(self.query_string)
        self.form  = MultiDict()
        self.files = {}
        self.json  = None
        self.data  = b""
        self.cookies = parse_cookies(self.headers.get("cookie", ""))

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def content_type(self):
        return self.headers.get("content-type", "")

    @property
    def content_length(self):
        try:
            return int(self.headers.get("content-length", 0))
        except ValueError:
            return 0

    @property
    def is_json(self):
        return "application/json" in self.content_type

    @property
    def is_secure(self):
        return self.headers.get("x-forwarded-proto", "http").lower() == "https"

    @property
    def host(self):
        return self.headers.get("host", "")

    @property
    def url(self):
        if self._url is None:
            scheme = "https" if self.is_secure else "http"
            self._url = "%s://%s%s" % (scheme, self.host, self.full_path)
        return self._url

    @property
    def base_url(self):
        scheme = "https" if self.is_secure else "http"
        return "%s://%s%s" % (scheme, self.host, self.path)

    @property
    def referrer(self):
        return self.headers.get("referer") or self.headers.get("referrer")

    @property
    def user_agent(self):
        return self.headers.get("user-agent", "")

    @property
    def accept(self):
        return self.headers.get("accept", "")

    @property
    def authorization(self):
        """Return the raw Authorization header value."""
        return self.headers.get("authorization")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_json(self, force=False, silent=True):
        """
        Parse and return the JSON body.
        *force*  – parse even if Content-Type is not application/json.
        *silent* – return None on error instead of raising.
        """
        if not force and not self.is_json:
            return None
        try:
            return _json.loads(self.data.decode())
        except Exception as exc:
            if silent:
                return None
            raise exc

    def get_data(self, as_text=False):
        """Return raw body bytes (or str if *as_text* is True)."""
        if as_text:
            try:
                return self.data.decode()
            except Exception:
                return self.data.decode("latin-1")
        return self.data

    def values(self):
        """Combined dict of args and form (args take priority)."""
        merged = {}
        merged.update(self.form.to_dict())
        merged.update(self.args.to_dict())
        return merged

    def __repr__(self):
        return "<%s %s>" % (self.method, self.path)
