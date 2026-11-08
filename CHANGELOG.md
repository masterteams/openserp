# Changelog

## Unreleased

- Redesigned `search.html` with professional responsive search cards, thumbnails, API-response caching, retry-safe 200-item UI pagination and batch-merged JSON import; added a UTF-8 sample CSV under `batch-search/` and focused Node UI tests.
- Added standard-library Python CSV batch search and independent JSON merge tools, with per-query outputs, run manifests, failure accounting and focused tests.
- Added a dependency-free, direct-open `search.html` search UI for multi-engine video/web results and offline JSON parsing, with clearly labeled unknown/unverified video metadata.
- Added an opt-in local Docker Compose build override without changing the existing `docker-compose.yaml`.
- Added `install.sh` to build OpenSERP from the current directory, start it in Docker, and wait for a healthy service.
- Added `deploy.sh` lifecycle commands: `start`, `stop`, `restart`, `status`, and `log`.
- Documented the source-built workflow and the existing publicly published API port.
