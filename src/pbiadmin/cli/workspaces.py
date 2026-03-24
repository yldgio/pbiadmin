import typer

app = typer.Typer(help="Workspace commands.")


@app.command("list")
def list_workspaces(
    profile: str = typer.Option("default", "--profile", help="Named auth profile."),
) -> None:
    """List all workspaces in the tenant."""
    typer.echo("Not yet implemented.")
