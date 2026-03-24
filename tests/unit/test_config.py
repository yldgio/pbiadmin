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
