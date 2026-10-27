"""Callin.io for AI agents: place real phone calls and read call results."""
from .client import Callin, CallinError, CallResult

__all__ = ["Callin", "CallinError", "CallResult"]
try:  # the installed distribution is the single source of the version number
    from importlib.metadata import version as _version
    __version__ = _version("callin")
except Exception:  # running from a source checkout
    __version__ = "0.0.0+source"
