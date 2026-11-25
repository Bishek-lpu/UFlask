# Templates

uFlask ships a **lightweight Jinja2-compatible template engine** written in pure Python — no `eval`, no imports — designed to work within the RAM constraints of the Raspberry Pi Pico W.

---

## Setup

By default, templates are loaded from the `templates/` directory:

```
your_project/
├── main.py
└── templates/
    ├── index.html
    ├── login.html
    └── dashboard.html
```

### Custom template directory

```python
from uflask import set_templates_dir

set_templates_dir("/flash/views")  # or any path on your filesystem
```

---

## Rendering a Template

```python
from uflask import render_template

@app.get("/")
def index(request):
    html = render_template(
        "index.html",         # filename inside templates/
        title  = "Home",
        user   = {"name": "Alice", "role": "admin"},
        items  = ["Sensor A", "Sensor B", "Sensor C"],
    )
    return html, 200, "text/html; charset=utf-8"
```

### Render from a string

```python
from uflask import render_string

tpl = "Hello {{ name }}! You have {{ count }} messages."
html = render_string(tpl, name="Alice", count=5)
# → "Hello Alice! You have 5 messages."
```

---

## Template Syntax

### `{{ variable }}` — Output

```html
<h1>{{ title }}</h1>
<p>Welcome, {{ user.name }}!</p>
<p>Role: {{ user.role }}</p>
```

Variables are **HTML-escaped** automatically — `<` becomes `&lt;`, preventing XSS.

### `{{ variable | raw }}` — Unescaped Output

```html
<!-- Use | raw only when you trust the content -->
<div class="content">{{ html_body | raw }}</div>
```

### Attribute access

```html
{{ user.name }}          <!-- object attribute -->
{{ config.debug }}       <!-- nested attribute -->
{{ stats.sensor.temp }}  <!-- deeply nested -->
```

---

## `{# comment #}` — Comments

Comments are removed from the output entirely:

```html
{# TODO: add pagination here #}
<ul>
  {% for item in items %}
  <li>{{ item }}</li>
  {% endfor %}
</ul>
```

---

## `{% if %}` — Conditionals

```html
{% if user.role == "admin" %}
  <a href="/admin">Admin Panel</a>
{% elif user.role == "mod" %}
  <a href="/mod">Mod Tools</a>
{% else %}
  <p>Welcome, {{ user.name }}</p>
{% endif %}
```

### Supported operators

| Operator | Example |
|---|---|
| `==` | `{% if status == "ok" %}` |
| `!=` | `{% if error != "" %}` |
| `>` | `{% if count > 0 %}` |
| `<` | `{% if temp < 100 %}` |
| `>=` | `{% if score >= 50 %}` |
| `<=` | `{% if level <= 3 %}` |
| `and` | `{% if a and b %}` |
| `or` | `{% if a or b %}` |
| `not` | `{% if not logged_in %}` |

### Truthy/falsy values

```html
{% if items %}          {# True when list is non-empty #}
{% if not items %}      {# True when list is empty or None #}
{% if user %}           {# True when user is not None #}
{% if count == 0 %}     {# Explicit zero check #}
```

### String comparisons

```html
{% if method == "POST" %}
{% if content_type == "application/json" %}
```

---

## `{% for %}` — Loops

```html
<ul>
  {% for item in items %}
  <li>{{ item }}</li>
  {% endfor %}
</ul>
```

### Loop over a list of objects

```html
<table>
{% for user in users %}
  <tr>
    <td>{{ user.id }}</td>
    <td>{{ user.name }}</td>
    <td>{{ user.email }}</td>
  </tr>
{% endfor %}
</table>
```

### Loop variables

Inside a `{% for %}` block, the special `loop` object is available:

| Variable | Type | Description |
|---|---|---|
| `loop.index` | `int` | Current iteration (1-based) |
| `loop.index0` | `int` | Current iteration (0-based) |
| `loop.first` | `bool` | `True` on the first iteration |
| `loop.last` | `bool` | `True` on the last iteration |

```html
<ol>
{% for item in items %}
  <li class="{% if loop.first %}first{% endif %}{% if loop.last %} last{% endif %}">
    {{ loop.index }}. {{ item }}
  </li>
{% endfor %}
</ol>
```

### Unpacking tuples / pairs

```html
{% for key, value in pairs %}
  <dt>{{ key }}</dt>
  <dd>{{ value }}</dd>
{% endfor %}
```

```python
# In your view:
return render_template("pairs.html", pairs=[("CPU", "RP2040"), ("RAM", "264kB")])
```

---

## `{% set %}` — Variable Assignment

```html
{% set greeting = "Good morning" %}
<p>{{ greeting }}, {{ user.name }}!</p>

{% set total = 0 %}
{% for item in cart %}
  {% set total = item.price %}
{% endfor %}
<p>Total: {{ total }}</p>
```

---

## Nesting Blocks

Conditionals and loops can be freely nested:

```html
{% for user in users %}
  {% if user.active %}
    <div class="user {% if user.role == "admin" %}admin{% endif %}">
      {{ loop.index }}. {{ user.name }}
    </div>
  {% endif %}
{% endfor %}
```

---

## Real-World Example

**`templates/dashboard.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{{ title }} – Pico Dashboard</title>
</head>
<body>
  <nav>
    <span>⚡ uFlask</span>
    <span>Logged in as <b>{{ username }}</b></span>
    <a href="/logout">Logout</a>
  </nav>

  <main>
    <h1>{{ title }}</h1>

    {% if error %}
    <div class="alert">{{ error }}</div>
    {% endif %}

    <section>
      <h2>Sensors ({{ sensors | raw }})</h2>
      {# sensors is an integer passed as | raw to avoid escaping quotes #}
    </section>

    <table>
      <thead>
        <tr><th>#</th><th>Name</th><th>Value</th><th>Status</th></tr>
      </thead>
      <tbody>
        {% for sensor in sensor_list %}
        <tr>
          <td>{{ loop.index }}</td>
          <td>{{ sensor.name }}</td>
          <td>{{ sensor.value }}</td>
          <td>
            {% if sensor.ok %}
              <span class="ok">✓ Normal</span>
            {% else %}
              <span class="warn">⚠ Alert</span>
            {% endif %}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </main>
</body>
</html>
```

**View:**

```python
@app.get("/dashboard")
def dashboard(request):
    sensors = [
        {"name": "Temperature", "value": "24.5°C", "ok": True},
        {"name": "Humidity",    "value": "61%",     "ok": True},
        {"name": "Pressure",    "value": "1032hPa", "ok": False},
    ]
    return render_template(
        "dashboard.html",
        title       = "Dashboard",
        username    = "admin",
        error       = "",
        sensors     = len(sensors),
        sensor_list = sensors,
    )
```

---

## Limitations vs. Full Jinja2

uFlask's template engine is a **subset** of Jinja2, designed to run with minimal RAM. The following are **not** supported:

| Jinja2 Feature | uFlask Support |
|---|---|
| `{{ x + y }}` arithmetic in templates | ❌ — do it in Python |
| `{% macro %}` / `{% call %}` | ❌ |
| `{% include %}` / `{% extends %}` | ❌ |
| Filters (`{{ name \| upper }}`) | ✅ only `\| raw` |
| `{% block %}` inheritance | ❌ |
| `loop.cycle()` | ❌ |
| `{% with %}` | ❌ — use `{% set %}` |

For complex logic, **compute in Python and pass the result as a context variable** — this is better practice anyway.
