import typer

app = typer.Typer(help="Tenant migration commands.")


@app.command("run")
def migrate_run(
    source: str = typer.Option(..., "--source", help="Source tenant profile."),
    target: str = typer.Option(..., "--target", help="Target tenant profile."),
) -> None:
    """Migrate content between tenants."""
    typer.echo("Not yet implemented.")
