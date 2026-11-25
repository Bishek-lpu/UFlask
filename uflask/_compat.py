# uflask/_compat.py
# CPython / MicroPython compatibility layer.
#
# MicroPython uses `uasyncio`, `ujson`, `uos` etc.
# CPython uses `asyncio`, `json`, `os`.
#
# This module is imported by other uFlask modules instead of the platform
# modules directly, so the library works on both runtimes.

import sys

MICROPYTHON = sys.implementation.name == "micropython"

# ---------------------------------------------------------------------------
# asyncio
# ---------------------------------------------------------------------------
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio                           # CPython standard library

# ---------------------------------------------------------------------------
# json
# ---------------------------------------------------------------------------
try:
    import ujson as json
except ImportError:
    import json

# ---------------------------------------------------------------------------
# os
# ---------------------------------------------------------------------------
try:
    import uos as os
except ImportError:
    import os

# ---------------------------------------------------------------------------
# gc
# ---------------------------------------------------------------------------
import gc

# ---------------------------------------------------------------------------
# time  (always available on both)
# ---------------------------------------------------------------------------
import time

# MicroPython has time.ticks_ms / ticks_diff; CPython does not.
if not hasattr(time, "ticks_ms"):
    import time as _time

    def ticks_ms():
        return int(_time.monotonic() * 1000)

    def ticks_diff(new, old):
        return new - old

    time.ticks_ms   = ticks_ms
    time.ticks_diff = ticks_diff

# ---------------------------------------------------------------------------
# sys.print_exception  (MicroPython) → traceback.print_exc (CPython)
# ---------------------------------------------------------------------------
if not hasattr(sys, "print_exception"):
    import traceback as _traceback
    import io as _io

    def _print_exception(exc, stream=None):
        buf = _io.StringIO()
        _traceback.print_exception(type(exc), exc, exc.__traceback__, file=buf)
        text = buf.getvalue()
        if stream is None:
            print(text, end="")
        else:
            stream.write(text)

    sys.print_exception = _print_exception

# ---------------------------------------------------------------------------
# asyncio.wait_for  (MicroPython 1.19 added this; stub for older firmware)
# ---------------------------------------------------------------------------
if not hasattr(asyncio, "wait_for"):
    async def _wait_for(coro, timeout):
        return await coro
    asyncio.wait_for = _wait_for

# ---------------------------------------------------------------------------
# TimeoutError  (MicroPython < 1.22 does not have it as a builtin)
# On MicroPython asyncio.TimeoutError IS the timeout exception;
# on CPython asyncio.TimeoutError is an alias for the builtin TimeoutError.
# We always use asyncio.TimeoutError in except clauses.
# ---------------------------------------------------------------------------
if not hasattr(asyncio, "TimeoutError"):
    # Very old MicroPython: define a stub so the except clause won't NameError
    class _TimeoutError(Exception):
        pass
    asyncio.TimeoutError = _TimeoutError

# Re-export so callers can do: from uflask._compat import asyncio, json, os
__all__ = ["asyncio", "json", "os", "gc", "time", "MICROPYTHON"]
