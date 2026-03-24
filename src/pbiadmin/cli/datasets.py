import typer

app = typer.Typer(help="Dataset commands.")


@app.command("list")
def list_datasets(
    profile: str = typer.Option("default", "--profile", help="Named auth profile."),
) -> None:
    """List all datasets in the tenant."""
    typer.echo("Not yet implemented.")
