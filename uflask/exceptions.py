# uflask/exceptions.py
# HTTP exceptions and global error handler registry for uFlask.
# Mirrors Flask's abort() / HTTPException / errorhandler pattern.

from .response import STATUS, Response


# ---------------------------------------------------------------------------
# Base HTTP exception
# ---------------------------------------------------------------------------

class HTTPException(Exception):
    """
    Raise this (or a subclass) from any handler or middleware to immediately
    return an HTTP error response.

    Usage::

        raise HTTPException(404, "User not found")
        # or use the abort() shortcut from response.py:
        from uflask import abort
        abort(403)
    """

    def __init__(self, status=500, description=None):
        self.status      = int(status)
        self.description = description or STATUS.get(self.status, "Error")
        super().__init__(self.description)

    def get_response(self):
        return Response(
            self.description,
            self.status,
            content_type="text/plain; charset=utf-8",
        )

    def __repr__(self):
        return "<HTTPException %d: %s>" % (self.status, self.description)


# ---------------------------------------------------------------------------
# Named exception subclasses (convenient, matches Flask)
# ---------------------------------------------------------------------------

class BadRequest(HTTPException):
    def __init__(self, description=None):
        super().__init__(400, description or "Bad Request")

class Unauthorized(HTTPException):
    def __init__(self, description=None):
        super().__init__(401, description or "Unauthorized")

class Forbidden(HTTPException):
    def __init__(self, description=None):
        super().__init__(403, description or "Forbidden")

class NotFound(HTTPException):
    def __init__(self, description=None):
        super().__init__(404, description or "Not Found")

class MethodNotAllowed(HTTPException):
    def __init__(self, allowed_methods=None, description=None):
        self.allowed_methods = allowed_methods or []
        desc = description or ("Method Not Allowed. Allowed: %s" % ", ".join(self.allowed_methods))
        super().__init__(405, desc)

class Conflict(HTTPException):
    def __init__(self, description=None):
        super().__init__(409, description or "Conflict")

class Gone(HTTPException):
    def __init__(self, description=None):
        super().__init__(410, description or "Gone")

class PayloadTooLarge(HTTPException):
    def __init__(self, description=None):
        super().__init__(413, description or "Payload Too Large")

class UnsupportedMediaType(HTTPException):
    def __init__(self, description=None):
        super().__init__(415, description or "Unsupported Media Type")

class UnprocessableEntity(HTTPException):
    def __init__(self, description=None):
        super().__init__(422, description or "Unprocessable Entity")

class TooManyRequests(HTTPException):
    def __init__(self, description=None, retry_after=None):
        self.retry_after = retry_after
        super().__init__(429, description or "Too Many Requests")

    def get_response(self):
        resp = super().get_response()
        if self.retry_after is not None:
            resp.headers["Retry-After"] = str(self.retry_after)
        return resp

class InternalServerError(HTTPException):
    def __init__(self, description=None):
        super().__init__(500, description or "Internal Server Error")

class NotImplemented_(HTTPException):
    """Use NotImplemented_ to avoid shadowing Python built-in."""
    def __init__(self, description=None):
        super().__init__(501, description or "Not Implemented")

class ServiceUnavailable(HTTPException):
    def __init__(self, description=None, retry_after=None):
        self.retry_after = retry_after
        super().__init__(503, description or "Service Unavailable")

    def get_response(self):
        resp = super().get_response()
        if self.retry_after is not None:
            resp.headers["Retry-After"] = str(self.retry_after)
        return resp


# ---------------------------------------------------------------------------
# Error handler registry
# ---------------------------------------------------------------------------

class ErrorHandlerRegistry:
    """
    Stores error handler callbacks registered via @app.errorhandler(code).

    Handlers are callables that receive the HTTPException (or any Exception)
    and should return a Response (or a value that _normalize can process).
    """

    def __init__(self):
        self._by_code  = {}   # int → callable
        self._by_type  = {}   # ExceptionType → callable

    def register(self, code_or_exc, handler):
        """
        Register *handler* for an HTTP status code or an exception class.

        handler(exc) → Response | str | tuple
        """
        if isinstance(code_or_exc, int):
            self._by_code[code_or_exc] = handler
        elif isinstance(code_or_exc, type) and issubclass(code_or_exc, Exception):
            self._by_type[code_or_exc] = handler
        else:
            raise TypeError("errorhandler() expects an int or an Exception subclass")

    def find(self, exc):
        """
        Return the most appropriate registered handler for *exc*, or None.

        Resolution order:
          1. Exact exception type (MRO walk)
          2. HTTP status code (for HTTPException subclasses)
        """
        # Walk MRO of the exception type
        for cls in type(exc).__mro__:
            if cls in self._by_type:
                return self._by_type[cls]

        # HTTP status code lookup
        if isinstance(exc, HTTPException):
            handler = self._by_code.get(exc.status)
            if handler:
                return handler

        # Catch-all 500
        return self._by_code.get(500)
