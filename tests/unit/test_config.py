"""Tests for pbiadmin.core.config — profile loading."""
import textwrap

import pytest

from pbiadmin.core.config import ProfileConfig, load_profile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PROFILES_TOML = textwrap.dedent("""\
    [tenants.prod]
    tenant_id = "aaa-prod"
    client_id  = "bbb-prod"
    auth_mode  = "service_principal"

    [tenants.dev]
    tenant_id = "ccc-dev"
    client_id  = "ddd-dev"
    auth_mode  = "interactive"
""")


@pytest.fixture()
def profiles_toml(tmp_path):
    path = tmp_path / "profiles.toml"
    path.write_text(PROFILES_TOML)
    return path


# ---------------------------------------------------------------------------
# Cycle 1 — Load valid profile
# ---------------------------------------------------------------------------

def test_load_profile_returns_profile_config(profiles_toml):
    profile = load_profile("prod", config_path=profiles_toml)
    assert isinstance(profile, ProfileConfig)
    assert profile.tenant_id == "aaa-prod"
    assert profile.client_id == "bbb-prod"
    assert profile.auth_mode == "service_principal"


# ---------------------------------------------------------------------------
# Cycle 2 — Client secret resolved from environment variable
# ---------------------------------------------------------------------------

def test_load_profile_resolves_client_secret_from_env(profiles_toml, monkeypatch):
    monkeypatch.setenv("PBIADMIN_PROD_CLIENT_SECRET", "mysecret")
    profile = load_profile("prod", config_path=profiles_toml)
    assert profile.client_secret == "mysecret"


def test_load_profile_client_secret_none_when_env_not_set(profiles_toml, monkeypatch):
    monkeypatch.delenv("PBIADMIN_PROD_CLIENT_SECRET", raising=False)
    profile = load_profile("prod", config_path=profiles_toml)
    assert profile.client_secret is None


# ---------------------------------------------------------------------------
# Cycle 3 — Missing profile raises ConfigError
# ---------------------------------------------------------------------------

def test_load_profile_raises_config_error_for_unknown_profile(profiles_toml):
    from pbiadmin.core.errors import ConfigError

    with pytest.raises(ConfigError) as exc_info:
        load_profile("nonexistent", config_path=profiles_toml)

    assert "nonexistent" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Review #30 — Config guard: missing file
# ---------------------------------------------------------------------------

def test_load_profile_raises_config_error_for_missing_file(tmp_path):
    from pbiadmin.core.errors import ConfigError

    with pytest.raises(ConfigError) as exc_info:
        load_profile("prod", config_path=tmp_path / "missing.toml")

    assert "not found" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Review #30 — Config guard: missing required fields
# ---------------------------------------------------------------------------

def test_load_profile_raises_config_error_for_missing_required_fields(tmp_path):
    from pbiadmin.core.errors import ConfigError

    bad_toml = tmp_path / "profiles.toml"
    bad_toml.write_text("[tenants.bad]\ntenant_id = \"t1\"\n")  # missing client_id, auth_mode

    with pytest.raises(ConfigError) as exc_info:
        load_profile("bad", config_path=bad_toml)

    assert "missing required fields" in str(exc_info.value).lower()
