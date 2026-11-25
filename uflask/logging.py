# uflask/logging.py
# Structured logger for uFlask on MicroPython / Raspberry Pi Pico W.
# API mirrors Python's standard logging module as closely as MicroPython allows.

import sys
from ._compat import gc, time  # noqa: F401 – platform shim

# ---------------------------------------------------------------------------
# Log level constants
# ---------------------------------------------------------------------------

DEBUG    = 10
INFO     = 20
WARNING  = 30
ERROR    = 40
CRITICAL = 50

# Aliases
WARN = WARNING

_LEVEL_NAMES = {
    DEBUG:    "DEBUG",
    INFO:     "INFO",
    WARNING:  "WARNING",
    ERROR:    "ERROR",
    CRITICAL: "CRITICAL",
}

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

_level    = DEBUG       # minimum level to emit
_log_file = None        # optional path; None means stdout only
_colorize = False       # ANSI colours (useful if connected to a colour terminal)

# ANSI colour codes
_COLORS = {
    DEBUG:    "\033[36m",   # Cyan
    INFO:     "\033[32m",   # Green
    WARNING:  "\033[33m",   # Yellow
    ERROR:    "\033[31m",   # Red
    CRITICAL: "\033[35m",   # Magenta
}
_RESET = "\033[0m"

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def set_level(level):
    """Set the minimum log level.  Pass one of DEBUG / INFO / WARNING / ERROR / CRITICAL."""
    global _level
    _level = level


def set_log_file(path=None):
    """
    Log to *path* in addition to stdout.
    Pass None to disable file logging.
    """
    global _log_file
    _log_file = path


def enable_color(enabled=True):
    """Enable or disable ANSI colour output."""
    global _colorize
    _colorize = enabled


# ---------------------------------------------------------------------------
# Internal emit
# ---------------------------------------------------------------------------

def _timestamp():
    try:
        t = time.localtime()
        return "%04d-%02d-%02d %02d:%02d:%02d" % (t[0], t[1], t[2], t[3], t[4], t[5])
    except Exception:
        return "----"


def _mem():
    try:
        return gc.mem_free() // 1024
    except Exception:
        return 0


def _emit(level, *items):
    if level < _level:
        return

    label   = _LEVEL_NAMES.get(level, "LOG")
    ts      = _timestamp()
    mem     = _mem()
    message = " ".join(str(i) for i in items)

    plain_line = "%s [%-8s %4dkB] %s" % (ts, label, mem, message)

    if _colorize:
        color = _COLORS.get(level, "")
        display_line = "%s%s%s" % (color, plain_line, _RESET)
    else:
        display_line = plain_line

    print(display_line)

    if _log_file:
        try:
            with open(_log_file, "a") as f:
                f.write(plain_line + "\n")
        except Exception as e:
            print("uflask.logging: cannot write to log file:", e)


# ---------------------------------------------------------------------------
# Public API  (matches standard logging)
# ---------------------------------------------------------------------------

def debug(*items):
    _emit(DEBUG, *items)

def info(*items):
    _emit(INFO, *items)

def warning(*items):
    _emit(WARNING, *items)

# alias
warn = warning

def error(*items):
    _emit(ERROR, *items)

def critical(*items):
    _emit(CRITICAL, *items)

def exception(msg, exc=None):
    """Log *msg* at ERROR level, then print the traceback of *exc* (or sys.exc_info)."""
    _emit(ERROR, msg)
    if exc is not None:
        sys.print_exception(exc)
    else:
        try:
            sys.print_exception(sys.exc_info()[1])
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Logger class  (for per-module named loggers)
# ---------------------------------------------------------------------------

class Logger:
    """
    Named logger.  Usage::

        log = Logger("mymodule")
        log.info("started")
        log.error("something went wrong", exc)
    """

    def __init__(self, name, level=None):
        self.name  = name
        self._level = level   # None → inherit global

    def _effective_level(self):
        return self._level if self._level is not None else _level

    def _emit(self, level, *items):
        if level < self._effective_level():
            return
        label   = _LEVEL_NAMES.get(level, "LOG")
        ts      = _timestamp()
        mem     = _mem()
        message = " ".join(str(i) for i in items)
        plain   = "%s [%-8s %4dkB] [%s] %s" % (ts, label, mem, self.name, message)

        if _colorize:
            color   = _COLORS.get(level, "")
            display = "%s%s%s" % (color, plain, _RESET)
        else:
            display = plain

        print(display)

        if _log_file:
            try:
                with open(_log_file, "a") as f:
                    f.write(plain + "\n")
            except Exception as e:
                print("Logger: cannot write to log file:", e)

    def set_level(self, level):
        self._level = level

    def debug(self, *items):    self._emit(DEBUG,    *items)
    def info(self, *items):     self._emit(INFO,     *items)
    def warning(self, *items):  self._emit(WARNING,  *items)
    def warn(self, *items):     self._emit(WARNING,  *items)
    def error(self, *items):    self._emit(ERROR,    *items)
    def critical(self, *items): self._emit(CRITICAL, *items)

    def exception(self, msg, exc=None):
        self._emit(ERROR, msg)
        if exc is not None:
            sys.print_exception(exc)
        else:
            try:
                sys.print_exception(sys.exc_info()[1])
            except Exception:
                pass

    def __repr__(self):
        return "<Logger %s>" % self.name


def getLogger(name):
    """Return a named Logger (always creates a new instance – no global registry to save RAM)."""
    return Logger(name)
