"""MSAL-backed token acquisition for pbiadmin.

``msal`` is imported **inside** each function so that tests can patch it
with ``mocker.patch("msal.ConfidentialClientApplication", ...)``.
"""
from __future__ import annotations

from pathlib import Path

from pbiadmin.core.config import ProfileConfig
from pbiadmin.core.errors import AuthError

_SCOPES = ["https://analysis.windows.net/powerbi/api/.default"]
_DEFAULT_CACHE_DIR = Path.home() / ".pbiadmin"


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
    cache_file = _dir / f"cache_{profile.profile_name}.bin"

    import msal  # noqa: PLC0415  (late import keeps it patchable)

    cache = msal.SerializableTokenCache()
    if cache_file.exists():
        cache.deserialize(cache_file.read_text())

    authority = f"https://login.microsoftonline.com/{profile.tenant_id}"

    if profile.auth_mode == "service_principal":
        result = _acquire_sp(profile, authority, cache, msal)
    elif profile.auth_mode == "interactive":
        result = _acquire_interactive(profile, authority, cache, msal)
    else:
        raise AuthError(f"Unknown auth_mode: {profile.auth_mode!r}")

    # Persist updated cache
    if cache.has_state_changed:
        cache_file.write_text(cache.serialize())

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
    """Interactive / device-code flow."""
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
    return app.acquire_token_interactive(scopes=_SCOPES)
