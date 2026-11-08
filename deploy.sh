#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  printf 'Usage: %s {start|stop|restart|status|log}\n' "${0##*/}"
}

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 2
fi

case "$1" in
  start|stop|restart|status|log) ;;
  -h|--help|help) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac

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

case "$1" in
  start)
    "${compose[@]}" up -d --no-build --pull never openserp
    ;;
  stop)
    "${compose[@]}" stop openserp
    ;;
  restart)
    "${compose[@]}" restart openserp
    ;;
  status)
    "${compose[@]}" ps --all openserp
    ;;
  log)
    "${compose[@]}" logs --follow --tail=100 openserp
    ;;
esac
