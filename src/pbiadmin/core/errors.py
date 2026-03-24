"""Custom exception types for pbiadmin."""
from __future__ import annotations


class ConfigError(Exception):
    """Raised when a configuration problem is detected (e.g. missing profile)."""


class AuthError(Exception):
    """Raised when token acquisition fails."""
