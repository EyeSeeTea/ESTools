# Security Assistant

Security Assistant is a CLI that orchestrates multiple security steps for a project:
1) CycloneDX BOM generation
2) Trivy scan of the BOM
3) Dependency-Track upload and finding retrieval
4) Snyk scan (runs last so its output stays visible)

It can run interactively or in fully non-interactive (`--forced`) mode.

## Prerequisites
- Python 3 available on your PATH (invoked as `python3`).
- Docker + Docker Compose (for local Dependency-Track runs).
- `npm` available if Snyk needs to be installed automatically.
- Optional tokens:
  - `DTRACK_API_KEY` (or stored via prompt) for Dependency-Track uploads/fetches.
  - `SNYK_TOKEN` (optional); in forced mode Snyk will skip auth if no token is set.

## Quick start example
Forced, remote Dependency-Track server, Node 20.19.0:
```bash
python3 security_assistant.py \
  -p /absolute/path/to/app/ \
  --node-version 20.19.0 \
  --dependency-track-server http://url:port/ \
  --forced
```

## Usage
```bash
python3 security_assistant.py [options]
```

Key options:
- `-p, --path APP_ROOT` Project root.
- `--forced` Fully non-interactive mode.
- `--node-version VERSION` Node version to use via nvm for BOM generation when no nvm default is configured.
- `--dependency-track-server URL` Use an existing Dependency-Track API base URL (skips local stack).
- `--show-dtrack-findings` Fetch Dependency-Track findings even if the upload step is skipped (e.g., existing BOM).
- `--project-name NAME` / `--project-version VERSION` Override detected metadata.
- `--no-bom` / `--no-trivy` / `--no-dtrack` / `--no-snyk` Skip specific steps.
- `--dtrack-api-port` / `--dtrack-ui-port` Ports when starting local Dependency-Track.

Run `python3 security_assistant.py --help` for the full list.

## Behavior notes
- Project metadata: name/version are read from `package.json`. If missing and no overrides are provided, you will be prompted (or forced mode will fail unless you supply them).
- Dependency-Track:
  - If the BOM upload returns HTTP 409, the assistant treats it as “already exists” and shows findings from the existing BOM.
  - `--show-dtrack-findings` lets you view findings without uploading a BOM in this run.
  - If you pass a URL pointing to the UI port (8080), it will automatically switch to the API port (8081).
- Snyk:
  - Runs last so its output remains visible.
  - In forced mode, if `SNYK_TOKEN` is absent it skips auth and attempts the scan (may fail if the CLI is not already authenticated).
- Summary: the final summary prints the Dependency-Track URL you provided (or localhost defaults) along with Snyk/Trivy notes.

## Typical flow
1) Generate `bom.json` (or reuse an existing one).
2) Scan the BOM with Trivy.
3) Upload BOM to Dependency-Track and fetch findings (or just fetch findings when requested).
4) Run `snyk test`.

Exit codes are non-zero in forced mode when a required step fails. Duplicate BOMs (HTTP 409) are treated as soft success so findings can still be displayed.
