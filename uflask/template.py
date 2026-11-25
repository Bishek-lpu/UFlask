# uflask/template.py
# Lightweight Jinja2-compatible template engine for MicroPython.
#
# Supported syntax
# ----------------
#   {{ variable }}              – variable substitution (auto-escaped)
#   {{ variable | raw }}        – unescaped output
#   {% if expr %}...{% endif %} – conditionals (== != < > <= >=, and/or/not)
#   {% elif expr %}             – else-if branch
#   {% else %}                  – else branch
#   {% for var in iterable %}...{% endfor %}  – iteration
#   {% set var = expr %}        – variable assignment
#   {# comment #}               – comments (stripped from output)
#   {{ loop.index }}            – 1-based loop counter inside {% for %}
#   {{ loop.index0 }}           – 0-based loop counter
#   {{ loop.first }}            – True on first iteration
#   {{ loop.last }}             – True on last iteration
#
# Template directory
# ------------------
#   render_template("index.html", title="Home", items=[1,2,3])
#   TEMPLATES_DIR is set to "templates" by default; override with
#   set_templates_dir("/flash/templates").


import os as _os

TEMPLATES_DIR = "templates"

def set_templates_dir(path):
    global TEMPLATES_DIR
    TEMPLATES_DIR = path


# ---------------------------------------------------------------------------
# HTML escaping
# ---------------------------------------------------------------------------

_HTML_ESCAPES = (
    ("&", "&amp;"),
    ("<", "&lt;"),
    (">", "&gt;"),
    ('"', "&quot;"),
    ("'", "&#39;"),
)

def _escape(value):
    s = str(value)
    for char, entity in _HTML_ESCAPES:
        s = s.replace(char, entity)
    return s


# ---------------------------------------------------------------------------
# Simple expression evaluator (no eval – MicroPython friendly)
# ---------------------------------------------------------------------------

def _resolve(expr, ctx):
    """
    Resolve a simple expression against *ctx* (a dict).
    Supports:
      - bare name:          user
      - attribute access:   user.name
      - dict subscript:     user["key"]  (simple key only)
      - comparison:         x == 1, x != "a", x > 0, x < 0, x >= 0, x <= 0
      - boolean not:        not x
      - boolean and/or:     x and y, x or y
      - integer/string literals
    """
    expr = expr.strip()

    # Boolean operators (split on first keyword surrounded by spaces)
    for op in (" and ", " or "):
        idx = expr.find(op)
        if idx >= 0:
            left  = _resolve(expr[:idx],           ctx)
            right = _resolve(expr[idx + len(op):], ctx)
            return (left and right) if op.strip() == "and" else (left or right)

    if expr.startswith("not "):
        return not _resolve(expr[4:], ctx)

    # Comparison operators
    for op in ("==", "!=", ">=", "<=", ">", "<"):
        idx = expr.find(op)
        if idx >= 0:
            lhs = _resolve(expr[:idx].strip(),           ctx)
            rhs = _resolve(expr[idx + len(op):].strip(), ctx)
            if op == "==": return lhs == rhs
            if op == "!=": return lhs != rhs
            if op == ">=": return lhs >= rhs
            if op == "<=": return lhs <= rhs
            if op == ">":  return lhs > rhs
            if op == "<":  return lhs < rhs

    # None / bool literals
    if expr == "None":  return None
    if expr == "True":  return True
    if expr == "False": return False

    # Integer literal
    try:
        return int(expr)
    except ValueError:
        pass

    # Float literal
    try:
        return float(expr)
    except ValueError:
        pass

    # String literal
    if (expr.startswith('"') and expr.endswith('"')) or \
       (expr.startswith("'") and expr.endswith("'")):
        return expr[1:-1]

    # Variable / attribute / dict lookup
    parts = expr.replace("[", ".").replace("]", "").replace('"', "").replace("'", "").split(".")
    value = ctx.get(parts[0])
    for part in parts[1:]:
        if value is None:
            return None
        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = getattr(value, part, None)
    return value


# ---------------------------------------------------------------------------
# Tokeniser
# ---------------------------------------------------------------------------

def _tokenise(source):
    """
    Yield (type, content) tuples from *source*.
    Types: 'text', 'var', 'block', 'comment'
    """
    i = 0
    n = len(source)
    while i < n:
        # Find next tag
        j = source.find("{", i)
        if j < 0 or j + 1 >= n:
            yield ("text", source[i:])
            break
        c = source[j + 1]
        if c == "{":        # {{ ... }}
            yield ("text",    source[i:j])
            end = source.find("}}", j + 2)
            if end < 0:
                yield ("text", source[j:])
                break
            yield ("var",     source[j + 2 : end].strip())
            i = end + 2
        elif c == "%":      # {% ... %}
            yield ("text",    source[i:j])
            end = source.find("%}", j + 2)
            if end < 0:
                yield ("text", source[j:])
                break
            yield ("block",   source[j + 2 : end].strip())
            i = end + 2
        elif c == "#":      # {# ... #}
            yield ("text",    source[i:j])
            end = source.find("#}", j + 2)
            if end < 0:
                i = n
                break
            yield ("comment", source[j + 2 : end])
            i = end + 2
        else:
            yield ("text", source[i : j + 1])
            i = j + 1


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

class _LoopCtx:
    """Provides loop.index, loop.index0, loop.first, loop.last."""
    def __init__(self, index, total):
        self.index  = index + 1
        self.index0 = index
        self.first  = index == 0
        self.last   = index == total - 1


def _render_tokens(tokens, ctx):
    """Walk *tokens* (a list) with an index pointer; return (output_str, next_index)."""
    out = []
    i   = 0
    while i < len(tokens):
        typ, content = tokens[i]
        i += 1

        if typ == "text":
            out.append(content)

        elif typ == "comment":
            pass  # strip comments

        elif typ == "var":
            # {{ expr }} or {{ expr | raw }}
            raw_output = False
            expr = content
            if "|" in content:
                parts = content.split("|", 1)
                expr  = parts[0].strip()
                filt  = parts[1].strip()
                if filt == "raw":
                    raw_output = True

            value = _resolve(expr, ctx)
            if raw_output:
                out.append("" if value is None else str(value))
            else:
                out.append("" if value is None else _escape(value))

        elif typ == "block":
            # ------- if / elif / else / endif -------
            if content.startswith("if "):
                cond = content[3:].strip()
                # Collect tokens for the if / elif / else branches
                branches    = [(cond, [])]  # list of (condition_expr, token_list)
                else_tokens = None
                depth = 1
                while i < len(tokens):
                    t2, c2 = tokens[i]
                    i += 1
                    if t2 == "block":
                        if c2.startswith("if "):
                            depth += 1
                            branches[-1][1].append((t2, c2))
                        elif c2 == "endif":
                            depth -= 1
                            if depth == 0:
                                break
                            else:
                                branches[-1][1].append((t2, c2))
                        elif depth == 1 and c2.startswith("elif "):
                            branches.append((c2[5:].strip(), []))
                        elif depth == 1 and c2 == "else":
                            else_tokens = []
                        elif depth == 1 and else_tokens is not None:
                            else_tokens.append((t2, c2))
                        else:
                            (else_tokens if else_tokens is not None else branches[-1][1]).append((t2, c2))
                    else:
                        (else_tokens if else_tokens is not None else branches[-1][1]).append((t2, c2))

                # Evaluate branches
                rendered = False
                for bcond, btokens in branches:
                    if _resolve(bcond, ctx):
                        out.append(_render_tokens(btokens, ctx)[0])
                        rendered = True
                        break
                if not rendered and else_tokens is not None:
                    out.append(_render_tokens(else_tokens, ctx)[0])

            # ------- for -------
            elif content.startswith("for ") and " in " in content:
                # {% for item in items %} or {% for k, v in items %}
                rest = content[4:].strip()
                var_part, _, iter_expr = rest.partition(" in ")
                var_part  = var_part.strip()
                iter_expr = iter_expr.strip()

                # Collect body tokens up to matching endfor
                body_tokens = []
                depth = 1
                while i < len(tokens):
                    t2, c2 = tokens[i]
                    i += 1
                    if t2 == "block":
                        if c2.startswith("for ") and " in " in c2:
                            depth += 1
                        elif c2 == "endfor":
                            depth -= 1
                            if depth == 0:
                                break
                    body_tokens.append((t2, c2))

                iterable = _resolve(iter_expr, ctx)
                if iterable:
                    items = list(iterable)
                    total = len(items)
                    for idx, item in enumerate(items):
                        child_ctx = dict(ctx)
                        child_ctx["loop"] = _LoopCtx(idx, total)
                        # Support "for k, v in dict.items()" style
                        if "," in var_part:
                            vnames = [v.strip() for v in var_part.split(",")]
                            for vi, vn in enumerate(vnames):
                                try:
                                    child_ctx[vn] = item[vi]
                                except Exception:
                                    child_ctx[vn] = None
                        else:
                            child_ctx[var_part] = item
                        out.append(_render_tokens(body_tokens, child_ctx)[0])

            # ------- set -------
            elif content.startswith("set ") and "=" in content:
                rest    = content[4:].strip()
                varname, _, valexpr = rest.partition("=")
                ctx[varname.strip()] = _resolve(valexpr.strip(), ctx)

            # Ignore endif / endfor / else / elif (consumed above)

    return "".join(out), i


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_template(filename, **context):
    """
    Load *filename* from TEMPLATES_DIR, render it with *context*, and
    return the resulting HTML string.

    Usage::

        html = render_template("index.html", title="Home", user=user_obj)
        return Response(html, content_type="text/html; charset=utf-8")
    """
    path = filename if _os.sep in filename else (TEMPLATES_DIR + "/" + filename)
    with open(path, "r") as f:
        source = f.read()
    return render_string(source, **context)


def render_string(source, **context):
    """Render a template *source* string directly (no file I/O)."""
    tokens = list(_tokenise(source))
    result, _ = _render_tokens(tokens, dict(context))
    return result
