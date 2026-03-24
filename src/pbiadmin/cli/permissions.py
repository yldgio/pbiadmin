import typer

app = typer.Typer(help="Permission commands.")


@app.command("list")
def list_permissions(
    profile: str = typer.Option("default", "--profile", help="Named auth profile."),
) -> None:
    """List all permissions in the tenant."""
    typer.echo("Not yet implemented.")
