## Problem Statement

Power BI / Microsoft Fabric tenant administrators have no unified, scriptable CLI to inventory, back up, restore, and migrate artifacts across workspaces and tenants. The existing options are either point-and-click in the PBI web portal (no automation), the PowerShell `MicrosoftPowerBIMgmt` module (incomplete coverage, no Fabric Gen2 support), or raw REST API calls written from scratch each time. This creates risk: manual processes are error-prone, migrations are slow and untraceable, and there is no repeatable way to snapshot a tenant's state before a change.

## Solution

`pbiadmin` is a Python CLI toolkit and Copilot agent skill set for Power BI / Microsoft Fabric tenant administration. It lets administrators list, download, upload, delete, copy, and migrate artifacts (reports, datasets, dashboards, dataflows, paginated reports) across workspaces and tenants, with structured output, profile-based multi-tenant auth, and full CI/CD integration.

## User Stories

### Inventory
1. As a PBI admin, I want to list all workspaces in a tenant so that I can audit what exists before making changes.
2. As a PBI admin, I want to list all reports in a workspace so that I can see what content is published.
3. As a PBI admin, I want to list all datasets/semantic models in a workspace so that I can track data dependencies.
4. As a PBI admin, I want to list all dashboards in a workspace so that I have a complete inventory.
5. As a PBI admin, I want to list all dataflows (Gen1 and Gen2) in a workspace so that I know what ETL exists.
6. As a PBI admin, I want to list all paginated reports in a workspace so that I can manage them separately.
7. As a PBI admin, I want to export inventory as JSON or CSV so that I can import it into other systems or audit tools.

### Backup / Download
8. As a PBI admin, I want to download all PBIX reports from a workspace so that I have a local backup before changes.
9. As a PBI admin, I want to download all datasets from a workspace so that I can restore them if needed.
10. As a PBI admin, I want to download all dataflows (Gen1 and Gen2) from a workspace so that I can version them.
11. As a PBI admin, I want to download all paginated reports (.rdl/.rdlx) from a workspace for safekeeping.
12. As a PBI admin, I want to download a metadata+tile snapshot of dashboards (even though no native PBIX export exists) so that I have a partial backup of dashboard layout.
13. As a PBI admin, I want a `manifest.json` written alongside every download so that I know exactly what was captured and when.
14. As a PBI admin, I want existing files to be skipped (with a warning) on re-download so that I don't accidentally overwrite a manually-edited file.
15. As a PBI admin, I want a `--force` flag that overwrites existing files (renaming them to `.bak`) so that I can refresh a backup without losing the previous copy.

### Restore / Upload
16. As a PBI admin, I want to upload a PBIX file to a workspace so that I can restore a backed-up report.
17. As a PBI admin, I want to publish a PBIX file to a workspace so that I can deploy a new report.
18. As a PBI admin, I want to upload a dataset definition to a workspace so that I can restore data connectivity.
19. As a PBI admin, I want to import a dataflow JSON into a workspace so that I can restore ETL pipelines.
20. As a PBI admin, I want to upload a paginated report file to a workspace so that I can restore operational reports.
21. As a PBI admin, I want failed uploads to be written to an `errors.json` log so that I can remediate them individually.

### Delete
22. As a PBI admin, I want to delete a specific report from a workspace so that I can clean up stale content.
23. As a PBI admin, I want delete operations to require explicit confirmation so that I never accidentally remove production content.

### Copy & Migrate
24. As a PBI admin, I want to copy a report within the same tenant (different workspace) so that I can promote content through environments.
25. As a PBI admin, I want to migrate reports and datasets from one workspace to another so that I can restructure tenant layout.
26. As a PBI admin, I want to migrate artifacts across tenants (using two named profiles) so that I can move content between dev and prod Entra tenants.
27. As a PBI admin, I want `pbiadmin migrate` to detect a Premium-less target workspace upfront and surface a clear error so that I'm not surprised by a failure mid-migration.
28. As a PBI admin, I want to rebind dataset connections after upload so that cross-tenant migrations work end-to-end.
29. As a PBI admin, I want `--artifact-types` to filter what gets migrated so that I can migrate only reports without touching datasets.
30. As a PBI admin, I want `--dry-run` on migrate to show what would happen without transferring anything so that I can validate the plan first.

### Permissions
31. As a PBI admin, I want to set a user's role in a workspace so that I can manage access at scale.
32. As a PBI admin, I want to set a service principal's role in a workspace so that I can grant automation accounts access.
33. As a PBI admin, I want workspace name-to-id resolution so that I don't have to look up GUIDs manually.

### Auth & Configuration
34. As a PBI admin, I want named profiles in `profiles.toml` so that I can switch between tenants with `--profile prod`.
35. As a PBI admin, I want secrets loaded from env vars (not config files) so that credentials are never committed to git.
36. As a PBI admin, I want Service Principal auth mode for CI/CD pipelines so that automation works unattended.
37. As a PBI admin, I want interactive (device-code) auth mode for developer workstations so that I can authenticate with my own account.
38. As a PBI admin, I want token caching per profile so that I'm not prompted to re-authenticate on every command.

### Output & Observability
39. As a PBI admin, I want a rich table output by default so that I can read results at a glance in my terminal.
40. As a PBI admin, I want `--format json` output so that I can pipe results into `jq` or other tools.
41. As a PBI admin, I want `--format csv` output so that I can import results into Excel.
42. As a PBI admin, I want a structured `errors.json` per run so that I can identify exactly which items failed and why.
43. As a PBI admin, I want a `summary.json` per run (attempted/succeeded/failed/skipped counts) so that I can report on bulk operations.
44. As a PBI admin, I want `--verbose` mode to print HTTP request/response details so that I can debug API issues.
45. As a PBI admin, I want rate-limit (HTTP 429) handling with automatic backoff so that bulk operations complete without manual retries.
46. As a PBI admin, I want `--fail-fast` to abort on first error so that CI pipelines don't silently accumulate failures.

### CI/CD & Automation
47. As a DevOps engineer, I want a thin PowerShell wrapper (`pbiadmin.ps1`) so that I can call `pbiadmin` from Azure DevOps YAML pipelines without switching shells.
48. As a DevOps engineer, I want `PBIADMIN_PROFILE` env var support so that pipelines can select a profile without passing flags.

### Copilot Skills
49. As a developer using GitHub Copilot, I want a `pbi-list` skill so that I can ask "list all reports in workspace X" in natural language.
50. As a developer using GitHub Copilot, I want a `pbi-download` skill so that I can trigger a workspace backup via chat.
51. As a developer using GitHub Copilot, I want a `pbi-upload` skill so that I can restore artifacts via chat.
52. As a developer using GitHub Copilot, I want a `pbi-migrate` skill so that I can orchestrate cross-workspace migrations via chat.
53. As a developer using GitHub Copilot, I want a `pbi-permissions` skill so that I can manage workspace roles via chat.

## Implementation Decisions

### Language & Runtime
- Python 3.11+ only. `semantic-link`/`sempy` (required for Fabric Gen2 Dataflows) is Python-only, making Python the only viable single-language choice.
- Thin PowerShell wrapper scripts allowed only at the OS/CI boundary (not in the Python package).
- Package manager: `uv` with `pyproject.toml`. Replaces pip+venv.

### CLI Framework
- **Typer** for the CLI: auto-generated help, type validation, shell completion, subcommand groups.
- Root command: `pbiadmin`. Subcommand groups: `workspaces`, `reports`, `datasets`, `dashboards`, `dataflows`, `paginated`, `permissions`, `migrate`.

### Architecture — `src/` Layout
- `src/pbiadmin/` is the installable package. It cannot be imported without `uv pip install -e .`, preventing shadow imports.
- Layers: `cli/` (Typer commands) → `ops/` (operation logic) → `core/` (auth, client, config, output, errors) + `models/` (dataclasses) + `utils/` (retry, file helpers).

### Authentication
- `msal` Python library for all token acquisition (SP and interactive/device-code flows).
- Token caching per profile; automatic re-acquire on 401.
- Secrets never in config files — loaded from `PBIADMIN_{PROFILE}_CLIENT_SECRET` env vars or Azure Key Vault.

### Configuration
- `profiles.toml` stores non-secret profile config (tenant_id, client_id, auth_mode). Git-ignored by default; only `profiles.toml.example` committed.
- Profile selected via `--profile <name>` flag or `PBIADMIN_PROFILE` env var.

### API Layer
- PBI REST API (`requests`/`httpx`) for reports, datasets, dashboards, workspaces, permissions.
- `semantic-link`/`sempy` for Fabric Gen2 Dataflows; adapter pattern with REST fallback if sempy is incomplete.
- `fabric_client.py` isolated — no sempy imports in core `client.py`.

### File Output Structure
- `output/{tenant}/{workspace}/{artifact-type}/` — artifact files.
- `runs/{run_id}/errors.json` + `summary.json` — run logs.
- Conflict resolution: skip+warn (default), `--force` overwrites with `.bak`.

### Error Handling & Resilience
- Continue-on-error default for bulk operations; `--fail-fast` for CI.
- HTTP 429: exponential backoff with jitter, max 3 retries, capped at 60s.
- Structured error log: item id, artifact type, operation, HTTP status, message, timestamp.

### Skill Architecture
- Skills live in `.agent/skills/` (project-level, open-standards compatible).
- Five skills: `pbi-list`, `pbi-download`, `pbi-upload`, `pbi-migrate`, `pbi-permissions`.
- Each skill is a natural-language prompt that invokes `pbiadmin` CLI commands.

### Known Limitations
- Dashboards have no native PBIX export via PBI REST API. Export is metadata + tile JSON snapshot only.
- Fabric Gen2 Dataflows via sempy may lag PBI REST API feature parity; REST fallback documented.
- Importing PBIX to a workspace without Premium capacity will fail; `migrate` detects this upfront.
- Cross-tenant migration requires explicit post-upload `rebind` step for dataset connections.

## Testing Decisions

Good tests verify external behavior, not implementation details. A test should fail if and only if observable behavior changes.

### What to test
- **`core/auth.py`**: token acquisition for SP and interactive profiles (mock MSAL); missing profile raises clear error; token refresh on 401.
- **`core/config.py`**: loads valid `profiles.toml`; resolves secrets from env vars; rejects malformed config.
- **`core/client.py`**: injects Authorization header; retries on 429 with backoff; re-acquires token on 401.
- **`utils/retry.py`**: backoff timing, max retries, jitter bounds.
- **`core/output.py`**: table/JSON/CSV renderers produce correct output for a given data set.
- **`ops/` modules**: each operation calls the expected REST endpoint with the expected payload (mock `client`).
- **`cli/` commands**: Typer command routing, flag validation, `--dry-run` produces no side effects.

### Testing framework
- `pytest` + `pytest-mock`. Test files mirror the source tree under `tests/unit/` and `tests/integration/`.
- Integration tests require real credentials and are opt-in (`pytest -m integration`).
- No tests for `scripts/` (PS wrapper) or `.agent/skills/` (SKILL.md files).

## Out of Scope

- **Publishing to PyPI**: `pbiadmin` is a local admin tool, not a public library.
- **GUI or web interface**: CLI only.
- **Power BI Embedded / embed tokens**: not an admin use case.
- **Report rendering / screenshot capture**: not an artifact management operation.
- **Data-plane operations** (running queries, refreshing datasets via schedule): covered by existing PBI tooling.
- **Fabric items beyond Dataflows Gen2** (Lakehouses, Notebooks, Pipelines): future scope.
- **Workspace creation/deletion**: future scope.
- **Tenant-level settings** (capacity management, gateway config): future scope.
- **Windows-only features**: the Python package is cross-platform; only `scripts/pbiadmin.ps1` is Windows/PS-specific.

## Further Notes

- `pbi-tools` (by Bernat Agulló) is an existing third-party tool — the CLI root command must remain `pbiadmin`.
- Design document: `pbiadmin-design.md` in repo root (full pre-mortem session output).

### Child slices (implementation work items)

- #16 — S1: Project scaffold
- #17 — S2: Auth & profile config
- #18 — S3: REST API client + retry
- #19 — S4: Workspace listing (first working command)
- #20 — S5: Reports operations
- #21 — S6: Datasets operations
- #22 — S7: Dashboards operations
- #23 — S8: Dataflows Gen1 operations
- #24 — S9: Dataflows Gen2 / Fabric operations
- #25 — S10: Paginated Reports operations
- #26 — S11: Permissions management
- #27 — S12: Migration orchestration
- #28 — S13: Agent skills
- #29 — S14: PowerShell CI wrapper