import pbiadmin
from typer.testing import CliRunner
from pbiadmin.cli.main import app


def test_version():
    assert pbiadmin.__version__ == "0.1.0"


def test_cli_help_exits_zero():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0


def test_cli_help_lists_all_subcommand_groups():
    result = CliRunner().invoke(app, ["--help"])
    for group in [
        "workspaces",
        "reports",
        "datasets",
        "dashboards",
        "dataflows",
        "paginated",
        "permissions",
        "migrate",
    ]:
        assert group in result.output, f"'{group}' not found in --help output"
