import typer

app = typer.Typer(help="Paginated report commands.")


@app.command("list")
def list_paginated(
    profile: str = typer.Option("default", "--profile", help="Named auth profile."),
) -> None:
    """List all paginated reports in the tenant."""
    typer.echo("Not yet implemented.")
