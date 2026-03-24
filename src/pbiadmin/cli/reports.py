import typer

app = typer.Typer(help="Report commands.")


@app.command("list")
def list_reports(
    profile: str = typer.Option("default", "--profile", help="Named auth profile."),
) -> None:
    """List all reports in the tenant."""
    typer.echo("Not yet implemented.")
