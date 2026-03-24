"""Tests for pbiadmin.core.auth — token acquisition."""
from pathlib import Path

import pytest

from pbiadmin.core.auth import get_token
from pbiadmin.core.config import ProfileConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sp_profile(tmp_path: Path) -> ProfileConfig:
    return ProfileConfig(
        profile_name="prod",
        tenant_id="tenant-123",
        client_id="client-456",
        auth_mode="service_principal",
        client_secret="supersecret",
    )


def interactive_profile() -> ProfileConfig:
    return ProfileConfig(
        profile_name="dev",
        tenant_id="tenant-dev",
        client_id="client-dev",
        auth_mode="interactive",
    )


# ---------------------------------------------------------------------------
# Cycle 4 — Service-principal token acquisition
# ---------------------------------------------------------------------------

def test_get_token_sp_returns_access_token(tmp_path, mocker):
    mock_cache = mocker.MagicMock()
    mock_cache.has_state_changed = False  # skip file-write path
    mocker.patch("msal.SerializableTokenCache", return_value=mock_cache)

    mock_app = mocker.MagicMock()
    mock_app.acquire_token_silent.return_value = None
    mock_app.acquire_token_for_client.return_value = {
        "access_token": "tok123",
        "token_type": "Bearer",
    }
    mocker.patch("msal.ConfidentialClientApplication", return_value=mock_app)

    profile = sp_profile(tmp_path)
    token = get_token(profile, cache_dir=tmp_path)

    assert token == "tok123"
    mock_app.acquire_token_for_client.assert_called_once()


# ---------------------------------------------------------------------------
# Cycle 5 — Interactive token acquisition
# ---------------------------------------------------------------------------

def test_get_token_interactive_returns_access_token(tmp_path, mocker):
    mock_cache = mocker.MagicMock()
    mock_cache.has_state_changed = False
    mocker.patch("msal.SerializableTokenCache", return_value=mock_cache)

    mock_app = mocker.MagicMock()
    mock_app.get_accounts.return_value = []  # no cached accounts → go interactive
    mock_app.acquire_token_interactive.return_value = {
        "access_token": "interactive_tok",
        "token_type": "Bearer",
    }
    mocker.patch("msal.PublicClientApplication", return_value=mock_app)

    profile = interactive_profile()
    token = get_token(profile, cache_dir=tmp_path)

    assert token == "interactive_tok"
    mock_app.acquire_token_interactive.assert_called_once()


# ---------------------------------------------------------------------------
# Cycle 6 — Token cache: second call uses acquire_token_silent
# ---------------------------------------------------------------------------

def test_get_token_sp_uses_cache_on_second_call(tmp_path, mocker):
    """
    First call:  acquire_token_silent returns None  → falls through to acquire_token_for_client.
    Second call: acquire_token_silent returns cached token → acquire_token_for_client NOT called again.
    Total acquire_token_for_client calls across both get_token() calls == 1.
    """
    # Use a real SerializableTokenCache so that has_state_changed and
    # serialize/deserialize work correctly, but control the MSAL app mock.
    import msal as real_msal

    real_cache = real_msal.SerializableTokenCache()

    call_count = {"silent": 0}

    def fake_acquire_silent(scopes, account):
        call_count["silent"] += 1
        # First call: nothing cached.  Second call: return a token.
        if call_count["silent"] >= 2:
            return {"access_token": "cached_tok", "token_type": "Bearer"}
        return None

    mock_app = mocker.MagicMock()
    mock_app.acquire_token_silent.side_effect = fake_acquire_silent
    mock_app.acquire_token_for_client.return_value = {
        "access_token": "tok123",
        "token_type": "Bearer",
    }

    mock_cache_cls = mocker.patch("msal.SerializableTokenCache", return_value=real_cache)
    mocker.patch("msal.ConfidentialClientApplication", return_value=mock_app)

    profile = sp_profile(tmp_path)

    # First call — cold cache
    t1 = get_token(profile, cache_dir=tmp_path)
    # Second call — should hit silent path
    t2 = get_token(profile, cache_dir=tmp_path)

    assert t1 == "tok123"
    assert t2 == "cached_tok"
    assert mock_app.acquire_token_for_client.call_count == 1
