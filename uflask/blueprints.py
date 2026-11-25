# uflask/blueprints.py
# Blueprint support for uFlask – mirrors Flask's Blueprint class.
#
# Blueprints let you split a large application into logical components
# (e.g. auth, api, admin) each in their own file, then register them
# on the main UFlask app.
#
# Usage
# -----
#   # auth.py
#   from uflask import Blueprint
#
#   auth = Blueprint("auth", url_prefix="/auth")
#
#   @auth.route("/login", methods=["GET", "POST"])
#   def login(request):
#       ...
#
#   @auth.before_request
#   def check_auth(request):
#       ...  # return Response to short-circuit
#
#   # main.py
#   from uflask import UFlask
#   from auth import auth
#
#   app = UFlask(__name__)
#   app.register_blueprint(auth)


class Blueprint:
    """
    A named collection of routes and hooks that can be registered on a UFlask app.

    Parameters
    ----------
    name        : str  – unique name for this blueprint
    url_prefix  : str  – path prefix prepended to all routes (default "")
    """

    def __init__(self, name, url_prefix=""):
        self.name        = name
        self.url_prefix  = url_prefix.rstrip("/")
        self._routes     = []   # list of (path, handler, methods)
        self._before     = []
        self._after      = []
        self._teardown   = []

    # ------------------------------------------------------------------
    # Route decorators
    # ------------------------------------------------------------------

    def route(self, path, methods=None):
        methods = methods or ["GET"]
        if isinstance(methods, str):
            methods = [methods]
        methods = [m.upper() for m in methods]

        def decorator(fn):
            self._routes.append((path, fn, methods))
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

    # ------------------------------------------------------------------
    # Hook decorators
    # ------------------------------------------------------------------

    @property
    def before_request(self):
        def decorator(fn):
            self._before.append(fn)
            return fn
        return decorator

    @property
    def after_request(self):
        def decorator(fn):
            self._after.append(fn)
            return fn
        return decorator

    @property
    def teardown_request(self):
        def decorator(fn):
            self._teardown.append(fn)
            return fn
        return decorator

    # ------------------------------------------------------------------
    # Internal: called by UFlask.register_blueprint()
    # ------------------------------------------------------------------

    def _register(self, app):
        """Attach this blueprint's routes and hooks to *app*."""
        for path, fn, methods in self._routes:
            full_path = self.url_prefix + path
            # Give the handler the blueprint name in its qualified name
            fn._bp_name = self.name
            app._add_route(full_path, fn, methods)

        for fn in self._before:
            app.middleware.add_before(fn)
        for fn in self._after:
            app.middleware.add_after(fn)
        for fn in self._teardown:
            app.middleware.add_teardown(fn)

    def __repr__(self):
        return "<Blueprint %r prefix=%r routes=%d>" % (
            self.name, self.url_prefix, len(self._routes)
        )
