# tests/test_request.py
"""Tests for uflask.request — runs on CPython (no MicroPython APIs used)."""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from uflask.request import (
    Request, MultiDict, parse_query_string,
    _decode_percent, _parse_multidict,
)


# ---------------------------------------------------------------------------
# _decode_percent
# ---------------------------------------------------------------------------

class TestDecodePercent:
    def test_plain(self):
        assert _decode_percent("hello") == "hello"

    def test_space_plus(self):
        assert _decode_percent("hello+world") == "hello world"

    def test_percent_encoding(self):
        assert _decode_percent("caf%C3%A9") == "café"

    def test_percent_encoding_space(self):
        assert _decode_percent("hello%20world") == "hello world"

    def test_invalid_percent(self):
        # Should not raise
        result = _decode_percent("100%")
        assert "100" in result


# ---------------------------------------------------------------------------
# parse_query_string
# ---------------------------------------------------------------------------

class TestParseQueryString:
    def test_empty(self):
        assert parse_query_string("") == {}

    def test_single(self):
        assert parse_query_string("key=value") == {"key": "value"}

    def test_multiple(self):
        result = parse_query_string("a=1&b=2&c=3")
        assert result == {"a": "1", "b": "2", "c": "3"}

    def test_no_value(self):
        result = parse_query_string("flag")
        assert result == {"flag": ""}

    def test_encoded_key_value(self):
        result = parse_query_string("my+key=hello%20world")
        assert result == {"my key": "hello world"}


# ---------------------------------------------------------------------------
# MultiDict
# ---------------------------------------------------------------------------

class TestMultiDict:
    def test_basic_add_get(self):
        md = MultiDict()
        md.add("key", "first")
        assert md["key"] == "first"

    def test_last_value_wins(self):
        md = MultiDict()
        md.add("key", "first")
        md.add("key", "second")
        assert md["key"] == "second"

    def test_getlist(self):
        md = MultiDict()
        md.add("tag", "python")
        md.add("tag", "web")
        md.add("tag", "pico")
        assert md.getlist("tag") == ["python", "web", "pico"]

    def test_getlist_missing(self):
        md = MultiDict()
        assert md.getlist("missing") == []

    def test_getlist_default(self):
        md = MultiDict()
        assert md.getlist("x", default=None) is None

    def test_to_dict(self):
        md = MultiDict()
        md.add("a", "1")
        md.add("b", "2")
        assert md.to_dict() == {"a": "1", "b": "2"}


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class TestRequest:
    def _make(self, method="GET", uri="/", headers=None):
        return Request(method, uri, "HTTP/1.1", headers or {})

    def test_method_uppercased(self):
        r = self._make("get")
        assert r.method == "GET"

    def test_path_and_query(self):
        r = self._make(uri="/api/users?page=2&per_page=10")
        assert r.path == "/api/users"
        assert r.args["page"] == "2"
        assert r.args["per_page"] == "10"

    def test_content_type(self):
        r = self._make(headers={"content-type": "application/json"})
        assert r.content_type == "application/json"
        assert r.is_json is True

    def test_is_json_false(self):
        r = self._make(headers={"content-type": "text/html"})
        assert r.is_json is False

    def test_content_length(self):
        r = self._make(headers={"content-length": "42"})
        assert r.content_length == 42

    def test_content_length_missing(self):
        r = self._make()
        assert r.content_length == 0

    def test_cookies(self):
        r = self._make(headers={"cookie": "session=abc123; theme=dark"})
        assert r.cookies == {"session": "abc123", "theme": "dark"}

    def test_user_agent(self):
        r = self._make(headers={"user-agent": "TestAgent/1.0"})
        assert r.user_agent == "TestAgent/1.0"

    def test_authorization(self):
        r = self._make(headers={"authorization": "Bearer tok"})
        assert r.authorization == "Bearer tok"

    def test_host(self):
        r = self._make(headers={"host": "pico.local"})
        assert r.host == "pico.local"

    def test_get_json_valid(self):
        r = self._make(headers={"content-type": "application/json"})
        r.data = b'{"x": 1}'
        assert r.get_json() == {"x": 1}

    def test_get_json_invalid_silent(self):
        r = self._make(headers={"content-type": "application/json"})
        r.data = b"not-json"
        assert r.get_json(silent=True) is None

    def test_get_json_force(self):
        r = self._make(headers={"content-type": "text/plain"})
        r.data = b'{"forced": true}'
        assert r.get_json(force=True) == {"forced": True}

    def test_get_data_bytes(self):
        r = self._make()
        r.data = b"hello"
        assert r.get_data() == b"hello"

    def test_get_data_text(self):
        r = self._make()
        r.data = b"hello"
        assert r.get_data(as_text=True) == "hello"

    def test_repr(self):
        r = self._make("POST", "/submit")
        assert "POST" in repr(r)
        assert "/submit" in repr(r)

    def test_full_path(self):
        r = self._make(uri="/search?q=pico")
        assert r.full_path == "/search?q=pico"

    def test_values_merges(self):
        r = self._make(uri="/x?shared=from_query")
        r.form.add("shared", "from_form")
        r.form.add("form_only", "yes")
        v = r.values()
        # args take priority over form
        assert v["shared"] == "from_query"
        assert v["form_only"] == "yes"
