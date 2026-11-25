# uflask/middleware.py
# Middleware / hook system for uFlask.
# Mirrors Flask's before_request / after_request / teardown_request hooks
# and adds support for WSGI-style middleware callables.

# ---------------------------------------------------------------------------
# MiddlewareStack
# ---------------------------------------------------------------------------

class MiddlewareStack:
    """
    Manages the four groups of hook functions registered on UFlask:

    before_request    – called before the route handler; return a Response to
                        short-circuit the handler.
    after_request     – called after the route handler with (response,);
                        must return the (possibly modified) response.
    teardown_request  – always called; receives exc (or None); return value
                        is ignored.
    before_first_request – called once before the very first request is served.
    """

    def __init__(self):
        self._before          = []   # list[callable(request)]
        self._after           = []   # list[callable(request, response)]
        self._teardown        = []   # list[callable(request, exc_or_None)]
        self._before_first    = []   # list[callable()]
        self._first_request   = True

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def add_before(self, fn):
        """Register a before_request hook."""
        self._before.append(fn)

    def add_after(self, fn):
        """Register an after_request hook."""
        self._after.append(fn)

    def add_teardown(self, fn):
        """Register a teardown_request hook."""
        self._teardown.append(fn)

    def add_before_first(self, fn):
        """Register a before_first_request hook (called once only)."""
        self._before_first.append(fn)

    # ------------------------------------------------------------------
    # Execution (called by UFlask._handle)
    # ------------------------------------------------------------------

    async def run_before_first(self):
        """Execute before_first_request hooks if this is the first request."""
        if not self._first_request:
            return
        self._first_request = False
        for fn in self._before_first:
            result = fn()
            if hasattr(result, "send"):        # coroutine / generator
                import uasyncio as asyncio
                await asyncio.sleep(0)
                # Fire and forget – these hooks are rarely async on Pico W

    async def run_before(self, request):
        """
        Execute before_request hooks in registration order.
        Returns the first non-None Response (short-circuits), or None.
        """
        for fn in self._before:
            result = fn(request)
            if hasattr(result, "__await__"):
                import uasyncio as asyncio
                result = await result
            if result is not None:
                return result
        return None

    async def run_after(self, request, response):
        """
        Execute after_request hooks in registration order.
        Each hook receives (request, response) and MUST return a Response.
        """
        for fn in self._after:
            result = fn(request, response)
            if hasattr(result, "__await__"):
                import uasyncio as asyncio
                result = await result
            if result is not None:
                response = result
        return response

    async def run_teardown(self, request, exc=None):
        """Execute teardown hooks; exceptions inside are silently swallowed."""
        for fn in self._teardown:
            try:
                result = fn(request, exc)
                if hasattr(result, "__await__"):
                    import uasyncio as asyncio
                    result = await result
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Utility decorator helpers (used by UFlask to expose the Flask-style API)
# ---------------------------------------------------------------------------

def make_before_request_decorator(stack):
    def decorator(fn):
        stack.add_before(fn)
        return fn
    return decorator

def make_after_request_decorator(stack):
    def decorator(fn):
        stack.add_after(fn)
        return fn
    return decorator

def make_teardown_request_decorator(stack):
    def decorator(fn):
        stack.add_teardown(fn)
        return fn
    return decorator

def make_before_first_request_decorator(stack):
    def decorator(fn):
        stack.add_before_first(fn)
        return fn
    return decorator
