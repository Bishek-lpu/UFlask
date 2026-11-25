# tests/test_exceptions.py
"""Tests for uflask.exceptions."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from uflask.exceptions import (
    HTTPException, ErrorHandlerRegistry,
    BadRequest, Unauthorized, Forbidden, NotFound,
    MethodNotAllowed, Conflict, PayloadTooLarge,
    TooManyRequests, InternalServerError,
)
from uflask.response import Response


class TestHTTPException:
    def test_basic(self):
        exc = HTTPException(404, "Not here")
        assert exc.status == 404
        assert exc.description == "Not here"
        assert str(exc) == "Not here"

    def test_default_description(self):
        exc = HTTPException(500)
        assert "Internal" in exc.description

    def test_get_response(self):
        exc = HTTPException(400, "Bad input")
        resp = exc.get_response()
        assert isinstance(resp, Response)
        assert resp.status == 400
        assert "Bad input" in resp.body

    def test_named_bad_request(self):
        exc = BadRequest()
        assert exc.status == 400

    def test_named_not_found(self):
        exc = NotFound("Missing resource")
        assert exc.status == 404
        assert "Missing" in exc.description

    def test_method_not_allowed_includes_methods(self):
        exc = MethodNotAllowed(["GET", "POST"])
        assert "GET" in exc.description
        assert exc.status == 405

    def test_too_many_requests_retry_after(self):
        exc = TooManyRequests(retry_after=60)
        resp = exc.get_response()
        assert resp.headers.get("Retry-After") == "60"


class TestErrorHandlerRegistry:
    def test_register_by_code(self):
        reg = ErrorHandlerRegistry()
        handler = lambda exc: "handled"
        reg.register(404, handler)
        exc = NotFound()
        assert reg.find(exc) is handler

    def test_register_by_type(self):
        reg = ErrorHandlerRegistry()
        handler = lambda exc: "value-err"
        reg.register(ValueError, handler)
        exc = ValueError("bad")
        assert reg.find(exc) is handler

    def test_mro_resolution(self):
        reg = ErrorHandlerRegistry()
        base_handler = lambda exc: "base"
        reg.register(Exception, base_handler)
        # A TypeError (subclass of Exception) should resolve to base handler
        exc = TypeError("type err")
        assert reg.find(exc) is base_handler

    def test_no_handler_returns_none(self):
        reg = ErrorHandlerRegistry()
        assert reg.find(NotFound()) is None

    def test_fallback_500(self):
        reg = ErrorHandlerRegistry()
        handler = lambda exc: "500"
        reg.register(500, handler)
        exc = RuntimeError("crash")
        assert reg.find(exc) is handler

    def test_invalid_registration(self):
        reg = ErrorHandlerRegistry()
        with pytest.raises(TypeError):
            reg.register("not-a-code", lambda e: None)
