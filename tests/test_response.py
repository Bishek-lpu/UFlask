# tests/test_response.py
"""Tests for uflask.response."""

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from uflask.response import (
    Response, FileResponse, jsonify, redirect,
    make_response, STATUS, MIME,
)


class TestResponse:
    def test_defaults(self):
        r = Response()
        assert r.status == 200
        assert r.body == ""
        assert "text/html" in r.headers["Content-Type"]

    def test_custom_status(self):
        r = Response("Created", 201)
        assert r.status == 201

    def test_custom_content_type(self):
        r = Response("ok", content_type="text/plain")
        assert r.headers["Content-Type"] == "text/plain"

    def test_set_cookie_basic(self):
        r = Response()
        r.set_cookie("session", "abc123")
        assert "session=abc123" in r.headers["Set-Cookie"]
        assert "Path=/" in r.headers["Set-Cookie"]

    def test_set_cookie_max_age(self):
        r = Response()
        r.set_cookie("tok", "val", max_age=3600)
        assert "Max-Age=3600" in r.headers["Set-Cookie"]

    def test_set_cookie_secure_httponly(self):
        r = Response()
        r.set_cookie("x", "y", secure=True, httponly=True)
        h = r.headers["Set-Cookie"]
        assert "Secure" in h
        assert "HttpOnly" in h

    def test_set_cookie_multiple(self):
        r = Response()
        r.set_cookie("a", "1")
        r.set_cookie("b", "2")
        assert isinstance(r.headers["Set-Cookie"], list)
        assert len(r.headers["Set-Cookie"]) == 2

    def test_delete_cookie(self):
        r = Response()
        r.delete_cookie("session")
        h = r.headers["Set-Cookie"]
        assert "Max-Age=0" in h
        assert "1970" in h

    def test_set_header_chainable(self):
        r = Response()
        result = r.set_header("X-Custom", "value")
        assert result is r   # chainable
        assert r.headers["X-Custom"] == "value"

    def test_status_line(self):
        r = Response(status=404)
        assert r.status_line == "404 Not Found"

    def test_repr(self):
        r = Response(status=200)
        assert "200" in repr(r)


class TestJsonify:
    def test_dict(self):
        r = jsonify({"key": "value"})
        assert r.status == 200
        assert r.headers["Content-Type"] == "application/json"
        data = json.loads(r.body)
        assert data == {"key": "value"}

    def test_list(self):
        r = jsonify([1, 2, 3])
        assert json.loads(r.body) == [1, 2, 3]

    def test_custom_status(self):
        r = jsonify({}, status=201)
        assert r.status == 201

    def test_extra_headers(self):
        r = jsonify({}, headers={"X-Count": "5"})
        assert r.headers["X-Count"] == "5"


class TestRedirect:
    def test_default_302(self):
        r = redirect("/login")
        assert r.status == 302
        assert r.headers["Location"] == "/login"

    def test_301(self):
        r = redirect("/new", 301)
        assert r.status == 301


class TestMakeResponse:
    def test_basic(self):
        r = make_response("hello", 200)
        assert r.body == "hello"
        assert r.status == 200

    def test_with_content_type(self):
        r = make_response("ok", content_type="text/plain")
        assert r.headers["Content-Type"] == "text/plain"


class TestStatusAndMime:
    def test_common_statuses(self):
        assert STATUS[200] == "OK"
        assert STATUS[404] == "Not Found"
        assert STATUS[500] == "Internal Server Error"
        assert STATUS[204] == "No Content"

    def test_mime_types(self):
        assert "json" in MIME["json"]
        assert "text/html" in MIME["html"]
        assert MIME["png"] == "image/png"
