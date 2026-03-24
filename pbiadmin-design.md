# pbiadmin — Design Document

## Problem Statement

Create a modular, scriptable toolkit for Power BI / Microsoft Fabric tenant administration.
Primary use cases: inventory, backup/export, restore/import, and cross-workspace migration of
PBI artifacts across one or more tenants.

---

## Artifact Scope

| Artifact | Operations |
|---|---|
| Reports (PBIX) | List, Download, Upload, Delete, Copy, Publish |
| Paginated Reports (RDL/RDLX) | List, Download, Upload, Delete |
| Datasets / Semantic Models | List, Download, Upload, Delete, Rebind |
| Dashboards | List, Download (JSON), Upload (JSON), Delete |
| Dataflows Gen1 | List, Export (JSON), Import (JSON), Delete |
| Dataflows Gen2 (Fabric) | List, Export, Import, Delete |

Additional cross-cutting operations: Set workspace permissions, Copy within same tenant.

---

## Language & Tooling

- **Single implementation language: Python 3.11+**
  - Rationale: `semantic-link`/`sempy` (required for Fabric Gen2 Dataflows) is Python-only;
    MSAL Python handles multi-tenant auth cleanly; pytest ecosystem; cross-platform without PS Core.
- **Thin PowerShell wrapper scripts** are allowed only at OS/CI boundary (e.g., calling `pbiadmin`
  from Azure DevOps pipeline steps).
- **Package manager: `uv`** (`pyproject.toml`-based, replaces pip+venv).
- **CLI framework: Typer** (auto-generated help, type validation, shell completion).
- **Testing: pytest + pytest-mock**.

---

## CLI Interface

Root command: **`pbiadmin`**

```
pbiadmin workspaces list               --profile <name>
pbiadmin reports list                  --workspace <name|id> --profile <name>
pbiadmin reports download              --workspace <name|id> [--all | --name <n>] --output <dir> --profile <name>
pbiadmin reports upload                --file <path> --workspace <name|id> --profile <name>
pbiadmin reports delete                --workspace <name|id> --name <n> --profile <name>
pbiadmin reports copy                  --from-workspace <n> --to-workspace <n> --name <n> --profile <name>
pbiadmin reports publish               --file <path> --workspace <name|id> --profile <name>

pbiadmin datasets list/download/upload/delete/rebind   (same pattern)
pbiadmin dashboards list/download/upload/delete        (same pattern)
pbiadmin dataflows list/export/import/delete           (same pattern)
pbiadmin paginated list/download/upload/delete         (same pattern)
pbiadmin permissions set               --workspace <name|id> --principal <upn|sp> --role <Member|Contributor|Admin|Viewer>

pbiadmin migrate                       --from-profile <n> --to-profile <n> --workspace <name|id> [--artifact-types reports,datasets]
```

Global flags: `--profile`, `--output`, `--format [table|json|csv]`, `--fail-fast`, `--force`, `--dry-run`, `--verbose`

Output formats for list/inventory commands: **Table (rich)**, **JSON**, **CSV**.

---

## Authentication

| Mode | When used |
|---|---|
| Service Principal (client_id + tenant_id + client_secret) | CI/CD automation |
| Interactive (device code / browser) | Developer workstations |

- **Multi-tenant support**: each named profile targets a specific Entra tenant.
- Secrets **never** stored in config files. Loaded from environment variables or Azure Key Vault.
- Token acquisition: `msal` (Python) with token caching per profile.

---

## Configuration

### `profiles.toml` (non-secret config)
```toml
[tenants.prod]
tenant_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
client_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
auth_mode  = "service_principal"   # or "interactive"

[tenants.dev]
tenant_id = "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
client_id = "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
auth_mode  = "interactive"
```

### `.env` (secrets — git-ignored)
```
PBIADMIN_PROD_CLIENT_SECRET=...
PBIADMIN_DEV_CLIENT_SECRET=...
```

Named profile selected via `--profile prod` or `PBIADMIN_PROFILE` env var.

---

## File Output Structure

```
output/
  {tenant_name}/
    {workspace_name}/
      reports/          ← .pbix files
      paginated/        ← .rdl / .rdlx files
      datasets/         ← .pbids + metadata JSON
      dashboards/       ← JSON exports
      dataflows/        ← JSON definitions
      manifest.json     ← workspace inventory snapshot (id, name, modified, downloaded_at)
runs/
  {run_id}/
    errors.json         ← structured error log for the run
    summary.json        ← run stats (items attempted, succeeded, failed, skipped)
```

**Conflict resolution on download:**
- Default: skip if file exists + warn loudly in output.
- `--force` flag: overwrite (renames existing to `.bak` before overwriting).

---

## API Layer

| Purpose | Library |
|---|---|
| PBI REST API (reports, datasets, dashboards, workspaces, permissions) | `requests` / `httpx` (direct REST calls) |
| Fabric Gen2 Dataflows | `semantic-link` / `sempy` |
| Authentication (all tenants) | `msal` |
| Token caching | `msal` cache (per-profile encrypted cache) |

API base URL: `https://api.powerbi.com/v1.0/myorg/`

---

## Error Handling & Resilience

- **Bulk operations**: continue-on-error by default; collect all errors in `errors.json`.
- `--fail-fast` flag aborts on first error (for CI pipelines).
- **Rate limiting (HTTP 429)**: auto-detected; exponential backoff with jitter (max 3 retries, capped at 60s wait).
- **Structured error log** per run: item id, artifact type, operation, HTTP status, message, timestamp.

---

## Skill Architecture

Skills live in **`.agent/skills/`** (project-level, open-standards compatible).

| Skill | Description |
|---|---|
| `pbi-list` | Inventory workspaces and artifacts in a tenant |
| `pbi-download` | Export / backup artifacts to disk |
| `pbi-upload` | Import / restore artifacts from disk |
| `pbi-migrate` | Orchestrated cross-workspace or cross-tenant migration |
| `pbi-permissions` | Manage workspace membership and roles |

Each skill is a thin wrapper that calls `pbiadmin` CLI commands.
The skills provide natural-language prompts that guide Copilot to invoke the right `pbiadmin` subcommands.

---

## Project Layout

`src/` layout is used (modern Python standard). This prevents shadow imports — the package cannot
be found unless installed (`uv pip install -e .`), ensuring tests always run against the installed
artifact, not the raw source tree.

```
src/
  pbiadmin/                      ← installable package (what gets distributed)
    __init__.py
    cli/
      __init__.py
      main.py                    ← Typer app root
      workspaces.py
      reports.py
      datasets.py
      dashboards.py
      dataflows.py
      paginated.py
      permissions.py
      migrate.py
    core/
      auth.py                    ← MSAL token acquisition, multi-tenant
      config.py                  ← profiles.toml + .env loader
      client.py                  ← REST API client with rate-limit handling
      fabric_client.py           ← sempy / Fabric SDK wrapper
      output.py                  ← rich table / JSON / CSV rendering
      errors.py                  ← error model + run log writer
    models/
      workspace.py
      report.py
      dataset.py
      dashboard.py
      dataflow.py
    ops/
      download.py
      upload.py
      copy.py
      delete.py
      rebind.py
      permissions.py
    utils/
      files.py                   ← manifest.json, path helpers
      retry.py                   ← exponential backoff decorator

.agent/
  skills/                        ← project-level skills (not distributed)
    pbi-list.md
    pbi-download.md
    pbi-upload.md
    pbi-migrate.md
    pbi-permissions.md

scripts/                         ← thin PowerShell wrappers (OS boundary only, not distributed)
  pbiadmin.ps1

tests/                           ← not distributed
  unit/
  integration/

pyproject.toml                   ← includes: [tool.setuptools.packages.find] where = ["src"]
profiles.toml.example
.env.example
README.md
```

---

## Key Risks & Mitigations

| Risk | Mitigation |
|---|---|
| PBI REST API does not support export of all artifact types equally (e.g., dashboards have no native export) | Use metadata+tile JSON snapshot; document limitation clearly |
| Gen2 Dataflow sempy API may lag REST API feature parity | Wrap in adapter; fallback to REST where sempy is incomplete |
| Import of PBIX to a Premium-less workspace may fail | Detect workspace capacity at start; surface clear error |
| Cross-tenant migration requires re-binding data source credentials | `rebind` operation is explicit post-upload step; documented in migrate skill |
| Token expiry during long bulk operations | Token refresh handled in `client.py`; re-acquire if 401 received |
| `profiles.toml` accidentally committed with secrets | `.gitignore` `profiles.toml` by default; only `profiles.toml.example` is committed |

---

*Generated by GitHub Copilot CLI pre-mortem session — 2026-03-24*
