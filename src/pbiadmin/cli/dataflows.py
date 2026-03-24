import typer

app = typer.Typer(help="Dataflow commands.")


@app.command("list")
def list_dataflows(
    profile: str = typer.Option("default", "--profile", help="Named auth profile."),
) -> None:
    """List all dataflows in the tenant."""
    typer.echo("Not yet implemented.")
