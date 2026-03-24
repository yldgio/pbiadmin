"""Tests for the CLI --profile flag and PBIADMIN_PROFILE env var fallback."""
import pytest
from typer.testing import CliRunner

from pbiadmin.cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Cycle 7 — --profile flag and env-var fallback
# ---------------------------------------------------------------------------

def test_cli_profile_flag_accepted(monkeypatch):
    """--profile prod --help must exit 0 (flag recognised)."""
    monkeypatch.delenv("PBIADMIN_PROFILE", raising=False)
    result = runner.invoke(app, ["--profile", "prod", "--help"])
    assert result.exit_code == 0, result.output


def test_cli_profile_env_var_accepted(monkeypatch):
    """PBIADMIN_PROFILE=prod; --help must exit 0 (env var recognised)."""
    monkeypatch.setenv("PBIADMIN_PROFILE", "prod")
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0, result.output
