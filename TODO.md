# Tasks

## Local Docker deployment

- [~] **DEPLOY-001 — Install and manage OpenSERP from the current repository directory.**
  - Implemented: `install.sh` builds and waits for health; `deploy.sh` handles `start`, `stop`, `restart`, `status`, and `log`; local Compose override preserves original prebuilt-image workflow.
  - Checked: Bash syntax, YAML override parsing, and all command dispatch paths using a mocked Docker executable (including a path with spaces and invalid-input errors).
  - **Pending acceptance:** actual `./install.sh` build and `/health` check on a host running Docker Engine + Compose v2. Docker is unavailable in the current validation environment.
  - Follow-up: from the repository root on the target machine, run `./install.sh`, `./deploy.sh status`, and `curl -f http://127.0.0.1:7000/health`; verify lifecycle commands.
