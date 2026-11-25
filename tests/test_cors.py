# tests/test_cors.py
"""Tests for uflask.cors."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from uflask.cors import CORS
from uflask.request import Request
from uflask.response import Response


def _req(origin=None):
    headers = {}
    if origin:
        headers["origin"] = origin
    return Request("GET", "/api", "HTTP/1.1", headers)


def _mock_app():
    """Minimal object to receive app.cors = self."""
    class _App:
        cors = None
    return _App()


class TestCORSWildcard:
    def test_allow_any_origin(self):
        app = _mock_app()
        cors = CORS(app, origins="*")
        req  = _req("https://anywhere.com")
        resp = cors.apply(req, Response())
        assert resp.headers["Access-Control-Allow-Origin"] == "*"

    def test_no_origin_header(self):
        app = _mock_app()
        cors = CORS(app, origins="*")
        req  = _req(None)
        resp = cors.apply(req, Response())
        # No CORS headers should be added when no Origin header present
        assert "Access-Control-Allow-Origin" not in resp.headers

    def test_credentials_echoes_origin(self):
        app = _mock_app()
        cors = CORS(app, origins="*", credentials=True)
        req  = _req("https://frontend.com")
        resp = cors.apply(req, Response())
        # With credentials, must echo the specific origin, not *
        assert resp.headers["Access-Control-Allow-Origin"] == "https://frontend.com"
        assert resp.headers.get("Access-Control-Allow-Credentials") == "true"


class TestCORSWhitelist:
    def test_allowed_origin(self):
        app = _mock_app()
        cors = CORS(app, origins=["https://allowed.com"])
        req  = _req("https://allowed.com")
        resp = cors.apply(req, Response())
        assert resp.headers["Access-Control-Allow-Origin"] == "https://allowed.com"

    def test_blocked_origin(self):
        app = _mock_app()
        cors = CORS(app, origins=["https://allowed.com"])
        req  = _req("https://evil.com")
        resp = cors.apply(req, Response())
        assert "Access-Control-Allow-Origin" not in resp.headers

    def test_vary_header_set(self):
        app = _mock_app()
        cors = CORS(app, origins=["https://allowed.com"])
        req  = _req("https://allowed.com")
        resp = cors.apply(req, Response())
        assert resp.headers.get("Vary") == "Origin"


class TestCORSPreflight:
    def test_preflight_returns_204(self):
        app = _mock_app()
        cors = CORS(app, origins="*")
        req  = _req("https://frontend.com")
        resp = cors.preflight(req)
        assert resp is not None
        assert resp.status == 204

    def test_preflight_blocked_origin(self):
        app = _mock_app()
        cors = CORS(app, origins=["https://allowed.com"])
        req  = _req("https://evil.com")
        resp = cors.preflight(req)
        assert resp is None

    def test_preflight_includes_methods(self):
        app = _mock_app()
        cors = CORS(app, origins="*", methods=["GET", "POST"])
        req  = _req("https://f.com")
        resp = cors.preflight(req)
        assert "GET" in resp.headers["Access-Control-Allow-Methods"]
        assert "POST" in resp.headers["Access-Control-Allow-Methods"]

    def test_preflight_max_age(self):
        app = _mock_app()
        cors = CORS(app, origins="*", max_age=1800)
        req  = _req("https://f.com")
        resp = cors.preflight(req)
        assert resp.headers["Access-Control-Max-Age"] == "1800"
