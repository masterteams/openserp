# Changelog

## Unreleased

- Added a dependency-free, direct-open `search.html` search UI for multi-engine video/web results and offline JSON parsing, with clearly labeled unknown/unverified video metadata.
- Added an opt-in local Docker Compose build override without changing the existing `docker-compose.yaml`.
- Added `install.sh` to build OpenSERP from the current directory, start it in Docker, and wait for a healthy service.
- Added `deploy.sh` lifecycle commands: `start`, `stop`, `restart`, `status`, and `log`.
- Documented the source-built workflow and the existing publicly published API port.
