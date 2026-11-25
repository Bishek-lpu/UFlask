# uflask/cors.py
# Full-featured Cross-Origin Resource Sharing (CORS) support for uFlask.
# Mirrors flask-cors behaviour; integrates with uFlask middleware system.

class CORS:
    """
    Add CORS headers to every response.

    Usage::

        from uflask import UFlask, CORS

        app  = UFlask(__name__)
        cors = CORS(app, origins="*")

    Or with fine-grained control::

        cors = CORS(
            app,
            origins=["https://myfrontend.com", "http://localhost:3000"],
            methods=["GET", "POST"],
            allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
            expose_headers=["X-Total-Count"],
            credentials=True,
            max_age=3600,
        )

    Parameters
    ----------
    app            : UFlask        – the application to attach to
    origins        : str | list    – allowed origins; "*" means all
    methods        : list | None   – allowed HTTP methods
    allow_headers  : list | None   – headers the browser may send
    expose_headers : list | None   – headers the browser may read
    credentials    : bool          – set Access-Control-Allow-Credentials
    max_age        : int           – preflight cache lifetime (seconds)
    """

    _DEFAULT_METHODS = [
        "GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"
    ]
    _DEFAULT_ALLOW_HEADERS = [
        "Content-Type", "Authorization", "Accept",
        "X-Requested-With", "X-Request-ID",
    ]

    def __init__(
        self,
        app,
        origins="*",
        methods=None,
        allow_headers=None,
        expose_headers=None,
        credentials=False,
        max_age=600,
    ):
        self.origins        = origins
        self.methods        = methods        or self._DEFAULT_METHODS
        self.allow_headers  = allow_headers  or self._DEFAULT_ALLOW_HEADERS
        self.expose_headers = expose_headers or []
        self.credentials    = credentials
        self.max_age        = int(max_age)

        # Register ourselves on the app so it can call us
        app.cors = self

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_origin(self, request_origin):
        """
        Return the origin string to put in the response header, or None
        if the request origin is not allowed.
        """
        if not request_origin:
            return None

        if self.origins == "*":
            # Wildcard + credentials is forbidden by the spec;
            # echo the actual origin instead.
            if self.credentials:
                return request_origin
            return "*"

        allowed = (
            [self.origins] if isinstance(self.origins, str) else list(self.origins)
        )
        return request_origin if request_origin in allowed else None

    def _common_headers(self, origin):
        """Return the headers shared between normal and preflight responses."""
        h = {}
        h["Access-Control-Allow-Origin"]  = origin
        h["Access-Control-Allow-Methods"] = ", ".join(self.methods)
        h["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        h["Access-Control-Max-Age"]       = str(self.max_age)

        if self.expose_headers:
            h["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)

        if self.credentials:
            h["Access-Control-Allow-Credentials"] = "true"

        # Vary: Origin so proxies don't cache the wrong origin
        if origin != "*":
            h["Vary"] = "Origin"

        return h

    # ------------------------------------------------------------------
    # Public API (called by UFlask._handle)
    # ------------------------------------------------------------------

    def apply(self, request, response):
        """
        Append CORS headers to *response* for a normal (non-preflight) request.
        Returns the (possibly modified) response.
        """
        origin = _get_origin(request)
        resolved = self._resolve_origin(origin)
        if resolved is None:
            return response

        for k, v in self._common_headers(resolved).items():
            response.headers.setdefault(k, v)

        return response

    def preflight(self, request):
        """
        Build and return a 204 preflight response, or None if the origin
        is not allowed.
        """
        origin = _get_origin(request)
        resolved = self._resolve_origin(origin)
        if resolved is None:
            return None

        from .response import Response
        resp = Response("", status=204)
        resp.headers.update(self._common_headers(resolved))
        return resp

    def __repr__(self):
        return "<CORS origins=%r>" % self.origins


# ---------------------------------------------------------------------------
# Module-level helper so other modules don't have to import the class
# ---------------------------------------------------------------------------

def _get_origin(request):
    return request.headers.get("origin") or request.headers.get("Origin")
