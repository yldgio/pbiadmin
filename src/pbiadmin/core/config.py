"""Profile configuration loader for pbiadmin.

Reads ``profiles.toml`` (``[tenants.<name>]`` sections) and resolves
the optional client secret from an environment variable.
"""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from pbiadmin.core.errors import ConfigError

_DEFAULT_CONFIG_PATH = Path.home() / ".pbiadmin" / "profiles.toml"


@dataclass
class ProfileConfig:
    """Parsed profile entry from profiles.toml."""

    profile_name: str
    tenant_id: str
    client_id: str
    auth_mode: str
    client_secret: str | None = field(default=None)


def load_profile(
    profile_name: str,
    *,
    config_path: Path | None = None,
) -> ProfileConfig:
    """Load a named profile from *config_path* (default: ``~/.pbiadmin/profiles.toml``).

    Parameters
    ----------
    profile_name:
        The key under ``[tenants]`` in the TOML file (e.g. ``"prod"``).
    config_path:
        Path to the TOML file.  Defaults to ``~/.pbiadmin/profiles.toml``.

    Returns
    -------
    ProfileConfig
        Populated profile; ``client_secret`` resolved from the environment
        variable ``PBIADMIN_<PROFILE_NAME_UPPER>_CLIENT_SECRET`` if set.

    Raises
    ------
    ConfigError
        If *profile_name* is not found in the TOML file.
    """
    path = config_path or _DEFAULT_CONFIG_PATH

    with path.open("rb") as fh:
        data = tomllib.load(fh)

    tenants = data.get("tenants", {})
    if profile_name not in tenants:
        raise ConfigError(
            f"Profile '{profile_name}' not found in {path}. "
            f"Available profiles: {list(tenants.keys())}"
        )

    entry = tenants[profile_name]

    env_key = f"PBIADMIN_{profile_name.upper()}_CLIENT_SECRET"
    client_secret = os.environ.get(env_key)

    return ProfileConfig(
        profile_name=profile_name,
        tenant_id=entry["tenant_id"],
        client_id=entry["client_id"],
        auth_mode=entry["auth_mode"],
        client_secret=client_secret,
    )
