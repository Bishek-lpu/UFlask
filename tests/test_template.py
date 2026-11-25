# tests/test_template.py
"""Tests for the uFlask Jinja2-compatible template engine."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from uflask.template import render_string


class TestVariableSubstitution:
    def test_simple(self):
        out = render_string("Hello {{ name }}!", name="World")
        assert out == "Hello World!"

    def test_missing_key(self):
        out = render_string("{{ missing }}")
        assert out == ""

    def test_html_escaped(self):
        out = render_string("{{ code }}", code="<script>alert(1)</script>")
        assert "<script>" not in out
        assert "&lt;script&gt;" in out

    def test_raw_filter(self):
        out = render_string("{{ html | raw }}", html="<b>bold</b>")
        assert out == "<b>bold</b>"

    def test_integer(self):
        out = render_string("{{ count }}", count=42)
        assert out == "42"

    def test_none_becomes_empty(self):
        out = render_string("{{ x }}", x=None)
        assert out == ""


class TestComments:
    def test_stripped(self):
        out = render_string("{# this is a comment #}hello")
        assert "comment" not in out
        assert out == "hello"


class TestIfBlock:
    def test_simple_true(self):
        out = render_string("{% if x %}yes{% endif %}", x=True)
        assert out == "yes"

    def test_simple_false(self):
        out = render_string("{% if x %}yes{% endif %}", x=False)
        assert out == ""

    def test_else(self):
        out = render_string("{% if flag %}A{% else %}B{% endif %}", flag=False)
        assert out == "B"

    def test_elif(self):
        tpl = "{% if x == 1 %}one{% elif x == 2 %}two{% else %}other{% endif %}"
        assert render_string(tpl, x=1) == "one"
        assert render_string(tpl, x=2) == "two"
        assert render_string(tpl, x=3) == "other"

    def test_string_comparison(self):
        tpl = '{% if role == "admin" %}yes{% else %}no{% endif %}'
        assert render_string(tpl, role="admin") == "yes"
        assert render_string(tpl, role="user")  == "no"

    def test_nested_if(self):
        tpl = "{% if a %}{% if b %}both{% else %}a_only{% endif %}{% endif %}"
        assert render_string(tpl, a=True, b=True)  == "both"
        assert render_string(tpl, a=True, b=False) == "a_only"
        assert render_string(tpl, a=False, b=True) == ""


class TestForBlock:
    def test_simple_list(self):
        out = render_string("{% for x in items %}{{ x }}{% endfor %}", items=[1, 2, 3])
        assert out == "123"

    def test_loop_index(self):
        out = render_string(
            "{% for x in items %}{{ loop.index }}{% endfor %}",
            items=["a", "b", "c"],
        )
        assert out == "123"

    def test_loop_index0(self):
        out = render_string(
            "{% for x in items %}{{ loop.index0 }}{% endfor %}",
            items=["a", "b"],
        )
        assert out == "01"

    def test_loop_first_last(self):
        tpl = "{% for x in items %}{% if loop.first %}F{% endif %}{% if loop.last %}L{% endif %}{% endfor %}"
        out = render_string(tpl, items=[1, 2, 3])
        assert out == "FL"

    def test_empty_list(self):
        out = render_string("{% for x in items %}{{ x }}{% endfor %}", items=[])
        assert out == ""

    def test_object_attribute(self):
        class Item:
            def __init__(self, name):
                self.name = name
        out = render_string(
            "{% for item in items %}{{ item.name }},{% endfor %}",
            items=[Item("a"), Item("b")],
        )
        assert out == "a,b,"

    def test_dict_items(self):
        out = render_string(
            "{% for k, v in pairs %}{{ k }}={{ v }} {% endfor %}",
            pairs=[("x", 1), ("y", 2)],
        )
        assert "x=1" in out
        assert "y=2" in out


class TestSetBlock:
    def test_set(self):
        out = render_string("{% set x = 42 %}{{ x }}")
        assert out == "42"

    def test_set_then_use(self):
        out = render_string("{% set greeting = \"Hello\" %}{{ greeting }}!")
        assert out == "Hello!"
