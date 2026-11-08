# Tasks

## Local Docker deployment

- [~] **DEPLOY-001 — Install and manage OpenSERP from the current repository directory.**
  - Implemented: `install.sh` builds and waits for health; `deploy.sh` handles `start`, `stop`, `restart`, `status`, and `log`; local Compose override preserves original prebuilt-image workflow.
  - Checked: Bash syntax, YAML override parsing, and all command dispatch paths using a mocked Docker executable (including a path with spaces and invalid-input errors).
  - **Evidence:** user-supplied terminal log confirms on-host `./install.sh` built `openserp:local`, the container became healthy, and `GET /health` returned 200. Stop/restart behavior remains unverified on that host.
  - Follow-up: from the repository root on the target machine, run `./install.sh`, `./deploy.sh status`, and `curl -f http://127.0.0.1:7000/health`; verify lifecycle commands.

## Standalone search HTML

- [~] **UI-001 — Single-file browser UI for live and offline OpenSERP search results.**
  - Implemented: `search.html` opens as `file://`; searches selected engines with `/mega/search`, filters classified video/web results, displays metadata, pagination, partial engine failures, raw JSON and import/export.
  - PASS: JavaScript compile and 17 focused mocked-DOM/parser/security checks against the GitHub blob.
  - NOT RUN: real browser fetch against the user's Docker host (no access to its browser/network); user should verify once after pull.
  - Constraint: original API provides no guaranteed structured video duration/resolution. The UI does not invent these values.
