# tests/test_routing.py
"""Tests for UFlask routing — URL matching, parameter types, method checks."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from uflask.app import _Route
from uflask.request import Request


def _req(method, path):
    return Request(method.upper(), path, "HTTP/1.1")


class TestRouteLiteral:
    def test_exact_match(self):
        r = _Route("/health", lambda req: None, ["GET"])
        assert r.match(_req("GET", "/health")) == {}

    def test_no_match(self):
        r = _Route("/health", lambda req: None, ["GET"])
        assert r.match(_req("GET", "/other")) is None

    def test_root(self):
        r = _Route("/", lambda req: None, ["GET"])
        assert r.match(_req("GET", "/")) == {}

    def test_wrong_method(self):
        r = _Route("/health", lambda req: None, ["POST"])
        assert r.match(_req("GET", "/health")) is None

    def test_multiple_methods(self):
        r = _Route("/data", lambda req: None, ["GET", "POST"])
        assert r.match(_req("GET",  "/data")) == {}
        assert r.match(_req("POST", "/data")) == {}


class TestRouteVariables:
    def test_string_var(self):
        r = _Route("/users/<uid>", lambda req, uid: None, ["GET"])
        result = r.match(_req("GET", "/users/alice"))
        assert result == {"uid": "alice"}

    def test_int_var(self):
        r = _Route("/users/<int:uid>", lambda req, uid: None, ["GET"])
        result = r.match(_req("GET", "/users/42"))
        assert result == {"uid": 42}

    def test_int_var_reject_string(self):
        r = _Route("/users/<int:uid>", lambda req, uid: None, ["GET"])
        assert r.match(_req("GET", "/users/alice")) is None

    def test_float_var(self):
        r = _Route("/temp/<float:val>", lambda req, val: None, ["GET"])
        result = r.match(_req("GET", "/temp/36.6"))
        assert result == {"val": pytest.approx(36.6)}

    def test_path_var(self):
        r = _Route("/files/<path:filename>", lambda req, filename: None, ["GET"])
        result = r.match(_req("GET", "/files/a/b/c.txt"))
        assert result == {"filename": "a/b/c.txt"}

    def test_multiple_vars(self):
        r = _Route("/orgs/<org>/repos/<repo>", lambda req, org, repo: None, ["GET"])
        result = r.match(_req("GET", "/orgs/acme/repos/widget"))
        assert result == {"org": "acme", "repo": "widget"}

    def test_too_few_segments(self):
        r = _Route("/users/<int:uid>", lambda req, uid: None, ["GET"])
        assert r.match(_req("GET", "/users")) is None

    def test_too_many_segments(self):
        r = _Route("/users/<uid>", lambda req, uid: None, ["GET"])
        assert r.match(_req("GET", "/users/alice/extra")) is None


class TestUFlaskRouting:
    """Integration tests using UFlask directly (no network)."""

    def _make_app(self):
        # Import UFlask but monkey-patch the asyncio server so we never bind
        from uflask.app import UFlask
        return UFlask(__name__, port=9999)

    def test_route_decorator(self):
        app = self._make_app()

        @app.get("/ping")
        def ping(request):
            return "pong"

        assert len(app._routes) > 0

    def test_normalize_string(self):
        from uflask.app import UFlask
        from uflask.response import Response
        app = UFlask(__name__, port=9998, static_dir="")
        resp = app._normalize("hello")
        assert isinstance(resp, Response)
        assert "hello" in resp.body

    def test_normalize_tuple(self):
        from uflask.app import UFlask
        from uflask.response import Response
        app = UFlask(__name__, port=9997, static_dir="")
        resp = app._normalize(("body", 201))
        assert resp.status == 201

    def test_normalize_dict(self):
        from uflask.app import UFlask
        import json
        app = UFlask(__name__, port=9996, static_dir="")
        resp = app._normalize({"key": "val"})
        assert resp.headers["Content-Type"] == "application/json"
        assert json.loads(resp.body) == {"key": "val"}

    def test_normalize_none(self):
        from uflask.app import UFlask
        app = UFlask(__name__, port=9995, static_dir="")
        resp = app._normalize(None)
        assert resp.status == 204

    def test_url_for(self):
        from uflask.app import UFlask
        app = UFlask(__name__, port=9994, static_dir="")

        @app.get("/users/<int:uid>")
        def user_detail(request, uid):
            return str(uid)

        url = app.url_for("user_detail", uid=5)
        assert url == "/users/5"
