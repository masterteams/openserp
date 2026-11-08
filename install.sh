#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -ne 0 ]]; then
  printf 'Usage: %s\n' "${0##*/}" >&2
  exit 2
fi

project_dir="$(pwd -P)"
for file in Dockerfile docker-compose.yaml docker-compose.local.yaml config.yaml; do
  if [[ ! -f "${project_dir}/${file}" ]]; then
    printf 'Error: %s is missing in %s. Run this from the OpenSERP repository root.\n' "$file" "$project_dir" >&2
    exit 1
  fi
done

if ! command -v docker >/dev/null 2>&1; then
  echo 'Error: Docker CLI is not installed.' >&2
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo 'Error: Docker Compose v2 (docker compose) is required.' >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo 'Error: Cannot reach the Docker daemon. Check that Docker is running and your user has access.' >&2
  exit 1
fi

compose=(docker compose --project-directory "$project_dir" \
  -f "$project_dir/docker-compose.yaml" \
  -f "$project_dir/docker-compose.local.yaml")

"${compose[@]}" config --quiet
printf 'Building and starting OpenSERP from %s ...\n' "$project_dir"
if ! "${compose[@]}" up -d --build --pull never --wait --wait-timeout 180 openserp; then
  echo 'Error: OpenSERP did not start and become healthy. Inspect ./deploy.sh status and ./deploy.sh log.' >&2
  exit 1
fi

printf 'OpenSERP is healthy. Check http://127.0.0.1:7000/health\n'
