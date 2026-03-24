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
# Cycle 5 — Interactive / device-code token acquisition
# ---------------------------------------------------------------------------

def test_get_token_interactive_returns_access_token(tmp_path, mocker):
    mock_cache = mocker.MagicMock()
    mock_cache.has_state_changed = False
    mocker.patch("msal.SerializableTokenCache", return_value=mock_cache)

    mock_app = mocker.MagicMock()
    mock_app.get_accounts.return_value = []  # no cached accounts
    mock_app.initiate_device_flow.return_value = {
        "user_code": "ABCDE",
        "message": "Go to https://microsoft.com/devicelogin and enter ABCDE",
    }
    mock_app.acquire_token_by_device_flow.return_value = {
        "access_token": "device_tok",
        "token_type": "Bearer",
    }
    mocker.patch("msal.PublicClientApplication", return_value=mock_app)

    profile = interactive_profile()
    token = get_token(profile, cache_dir=tmp_path)

    assert token == "device_tok"
    mock_app.acquire_token_by_device_flow.assert_called_once()


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


# ---------------------------------------------------------------------------
# Review #30 — Disk persistence: cache file written and reloaded
# ---------------------------------------------------------------------------

def test_get_token_sp_persists_cache_to_disk_and_reloads(tmp_path, mocker):
    """
    Simulates two separate process invocations via FakeCache.
    First get_token(): cold cache → acquires fresh token → writes file.
    Second get_token(): new FakeCache deserialized from file → silent hit.
    acquire_token_for_client total call count == 1.
    """

    class FakeCache:
        def __init__(self) -> None:
            self.data: str | None = None
            self.has_state_changed: bool = False

        def serialize(self) -> str:
            return self.data or ""

        def deserialize(self, text: str) -> None:
            self.data = text
            self.has_state_changed = False

    mocker.patch("msal.SerializableTokenCache", side_effect=lambda: FakeCache())

    fresh_call_count: list[int] = [0]

    def make_app(*args, **kwargs):
        app_mock = mocker.MagicMock()
        cache: FakeCache | None = kwargs.get("token_cache")

        if cache is not None and cache.data:
            # Cache was loaded from disk → return silently
            app_mock.acquire_token_silent.return_value = {
                "access_token": "cached_tok",
                "token_type": "Bearer",
            }
        else:
            # Cold cache → fresh acquisition
            app_mock.acquire_token_silent.return_value = None

            def fresh_acquire(scopes):
                fresh_call_count[0] += 1
                if cache is not None:
                    cache.data = "acquired_token_data"
                    cache.has_state_changed = True
                return {"access_token": "tok123", "token_type": "Bearer"}

            app_mock.acquire_token_for_client.side_effect = fresh_acquire

        return app_mock

    mocker.patch("msal.ConfidentialClientApplication", side_effect=make_app)

    profile = sp_profile(tmp_path)

    t1 = get_token(profile, cache_dir=tmp_path)
    cache_file = tmp_path / "cache_prod.bin"
    assert cache_file.exists(), "Cache file must be written after first call"

    t2 = get_token(profile, cache_dir=tmp_path)

    assert t1 == "tok123"
    assert t2 == "cached_tok"
    assert fresh_call_count[0] == 1, "acquire_token_for_client must only be called once"


# ---------------------------------------------------------------------------
# Review #30 — SP auth requires client_secret
# ---------------------------------------------------------------------------

def test_get_token_sp_raises_auth_error_if_no_client_secret(tmp_path, mocker):
    from pbiadmin.core.errors import AuthError

    mock_cache = mocker.MagicMock()
    mock_cache.has_state_changed = False
    mocker.patch("msal.SerializableTokenCache", return_value=mock_cache)

    profile = ProfileConfig(
        profile_name="prod",
        tenant_id="tenant-123",
        client_id="client-456",
        auth_mode="service_principal",
        client_secret=None,
    )

    with pytest.raises(AuthError) as exc_info:
        get_token(profile, cache_dir=tmp_path)

    assert "PBIADMIN_PROD_CLIENT_SECRET" in str(exc_info.value)
