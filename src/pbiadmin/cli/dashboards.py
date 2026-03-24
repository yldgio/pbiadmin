import typer

app = typer.Typer(help="Dashboard commands.")


@app.command("list")
def list_dashboards(
    profile: str = typer.Option("default", "--profile", help="Named auth profile."),
) -> None:
    """List all dashboards in the tenant."""
    typer.echo("Not yet implemented.")
