# uflask/__init__.py
# Public API surface for the uFlask micro-framework.
# Import everything a user needs from a single namespace.
#
# Usage::
#
#     from uflask import UFlask, jsonify, render_template, CORS, Blueprint
#
#     app = UFlask(__name__, debug=True)

# -- Application --
from .app        import UFlask

# -- Response helpers --
from .response   import (
    Response,
    FileResponse,
    jsonify,
    redirect,
    send_file,
    make_response,
    abort,
    STATUS,
    MIME,
)

# -- Request --
from .request    import Request

# -- Template engine --
from .template   import render_template, render_string, set_templates_dir

# -- CORS --
from .cors       import CORS

# -- Blueprints --
from .blueprints import Blueprint

# -- Exceptions (re-exported for convenience) --
from .exceptions import (
    HTTPException,
    BadRequest,
    Unauthorized,
    Forbidden,
    NotFound,
    MethodNotAllowed,
    Conflict,
    Gone,
    PayloadTooLarge,
    UnsupportedMediaType,
    UnprocessableEntity,
    TooManyRequests,
    InternalServerError,
    ServiceUnavailable,
)

# -- Logging --
from . import logging
from .logging import getLogger

__version__ = "1.0.0"
__all__ = [
    # core
    "UFlask",
    # response
    "Response", "FileResponse", "jsonify", "redirect",
    "send_file", "make_response", "abort", "STATUS", "MIME",
    # request
    "Request",
    # templates
    "render_template", "render_string", "set_templates_dir",
    # cors
    "CORS",
    # blueprints
    "Blueprint",
    # exceptions
    "HTTPException", "BadRequest", "Unauthorized", "Forbidden",
    "NotFound", "MethodNotAllowed", "Conflict", "Gone",
    "PayloadTooLarge", "UnsupportedMediaType", "UnprocessableEntity",
    "TooManyRequests", "InternalServerError", "ServiceUnavailable",
    # logging
    "logging", "getLogger",
]
