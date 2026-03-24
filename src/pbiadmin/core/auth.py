"""MSAL-backed token acquisition for pbiadmin.

``msal`` is imported **inside** each function so that tests can patch it
with ``mocker.patch("msal.ConfidentialClientApplication", ...)``.
"""
from __future__ import annotations

import os
import re
import tempfile
import warnings
from pathlib import Path

from pbiadmin.core.config import ProfileConfig
from pbiadmin.core.errors import AuthError

_SCOPES = ["https://analysis.windows.net/powerbi/api/.default"]
_DEFAULT_CACHE_DIR = Path.home() / ".pbiadmin"


def _safe_profile_name(name: str) -> str:
    """Return a filesystem-safe version of *name* (item 4 — path traversal guard)."""
    return re.sub(r"[^\w-]", "_", name)


def get_token(
    profile: ProfileConfig,
    *,
    cache_dir: Path | None = None,
) -> str:
    """Acquire a bearer token for *profile*.

    Parameters
    ----------
    profile:
        Loaded ``ProfileConfig``; ``auth_mode`` drives which MSAL flow is used.
    cache_dir:
        Directory to store the per-profile MSAL token cache.
        Defaults to ``~/.pbiadmin/``; inject ``tmp_path`` in tests.

    Returns
    -------
    str
        Raw access token string.

    Raises
    ------
    AuthError
        If MSAL returns an error response or the response is missing
        ``access_token``.
    """
    _dir = cache_dir or _DEFAULT_CACHE_DIR
    _dir.mkdir(parents=True, exist_ok=True)

    # Item 4 — sanitize profile name before using in a filesystem path
    safe_name = _safe_profile_name(profile.profile_name)
    cache_file = _dir / f"cache_{safe_name}.bin"

    import msal  # noqa: PLC0415  (late import keeps it patchable)

    cache = msal.SerializableTokenCache()

    # Item 5 — guard corrupt cache: warn and continue with empty cache
    if cache_file.exists():
        try:
            cache.deserialize(cache_file.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            warnings.warn(
                f"Ignoring corrupt token cache at {cache_file}: {exc}",
                stacklevel=2,
            )

    authority = f"https://login.microsoftonline.com/{profile.tenant_id}"

    if profile.auth_mode == "service_principal":
        result = _acquire_sp(profile, authority, cache, msal)
    elif profile.auth_mode == "interactive":
        result = _acquire_interactive(profile, authority, cache, msal)
    else:
        raise AuthError(f"Unknown auth_mode: {profile.auth_mode!r}")

    # Item 5 — atomic write: write to temp then os.replace
    if cache.has_state_changed:
        tmp_fd, tmp_path_str = tempfile.mkstemp(dir=_dir, suffix=".bin.tmp")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
                fh.write(cache.serialize())
            os.replace(tmp_path_str, cache_file)
        except Exception:
            try:
                os.unlink(tmp_path_str)
            except OSError:
                pass
            raise

    if "access_token" not in result:
        raise AuthError(
            f"Token acquisition failed: {result.get('error_description', result)}"
        )
    return result["access_token"]


def _acquire_sp(
    profile: ProfileConfig,
    authority: str,
    cache: object,
    msal: object,
) -> dict:
    """Service-principal (client-credentials) flow."""
    # Item 6 — guard missing client_secret before constructing the MSAL app
    if profile.client_secret is None:
        raise AuthError(
            f"Service principal auth requires a client secret. "
            f"Set env var PBIADMIN_{profile.profile_name.upper()}_CLIENT_SECRET."
        )

    app = msal.ConfidentialClientApplication(
        client_id=profile.client_id,
        client_credential=profile.client_secret,
        authority=authority,
        token_cache=cache,
    )
    # Try silent (cached) first
    silent = app.acquire_token_silent(scopes=_SCOPES, account=None)
    if silent and "access_token" in silent:
        return silent
    return app.acquire_token_for_client(scopes=_SCOPES)


def _acquire_interactive(
    profile: ProfileConfig,
    authority: str,
    cache: object,
    msal: object,
) -> dict:
    """Device-code flow (item 7)."""
    app = msal.PublicClientApplication(
        client_id=profile.client_id,
        authority=authority,
        token_cache=cache,
    )
    accounts = app.get_accounts()
    if accounts:
        silent = app.acquire_token_silent(scopes=_SCOPES, account=accounts[0])
        if silent and "access_token" in silent:
            return silent

    # Item 7 — device-code flow replaces acquire_token_interactive
    flow = app.initiate_device_flow(scopes=_SCOPES)
    if "user_code" not in flow:
        raise AuthError(
            f"Failed to initiate device flow: {flow.get('error_description', flow)}"
        )
    print(flow["message"])  # prompts user: "Go to https://... and enter code XXXX"
    return app.acquire_token_by_device_flow(flow)
