import typer
from pbiadmin.cli import (
    workspaces,
    reports,
    datasets,
    dashboards,
    dataflows,
    paginated,
    permissions,
    migrate,
)

app = typer.Typer(
    name="pbiadmin",
    help="Power BI / Fabric tenant administration CLI.",
    no_args_is_help=True,
)

app.add_typer(workspaces.app, name="workspaces")
app.add_typer(reports.app, name="reports")
app.add_typer(datasets.app, name="datasets")
app.add_typer(dashboards.app, name="dashboards")
app.add_typer(dataflows.app, name="dataflows")
app.add_typer(paginated.app, name="paginated")
app.add_typer(permissions.app, name="permissions")
app.add_typer(migrate.app, name="migrate")


@app.callback()
def main(
    ctx: typer.Context,
    profile: str | None = typer.Option(
        None,
        "--profile",
        envvar="PBIADMIN_PROFILE",
        help="Profile name from profiles.toml (overrides PBIADMIN_PROFILE env var).",
    ),
) -> None:
    """Power BI / Fabric tenant administration CLI."""
    ctx.ensure_object(dict)
    ctx.obj["profile"] = profile


if __name__ == "__main__":
    app()
