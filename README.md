# pbiadmin

Power BI / Fabric tenant administration CLI built with Python + Typer + uv.

## Installation

```bash
uv venv
uv pip install -e ".[dev]"
```

## Usage

```bash
pbiadmin --help
pbiadmin workspaces list --profile prod
pbiadmin reports list --profile prod
pbiadmin migrate run --source prod --target dev
```

## Configuration

Copy `profiles.toml.example` → `profiles.toml` and fill in your tenant credentials.  
Copy `.env.example` → `.env` and fill in your client secrets.

## Running tests

```bash
pytest --tb=short -v
# Integration tests (require real credentials):
pytest -m integration --tb=short -v
```

## Project structure

```
src/pbiadmin/
  cli/        — Typer CLI entry points
  core/       — Auth, config, API client, output rendering
  models/     — Dataclasses for PBI artifacts
  ops/        — Business logic (download, upload, copy, delete, rebind)
  utils/      — File helpers, retry decorator
```
