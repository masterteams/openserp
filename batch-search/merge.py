#!/usr/bin/env python3
"""Combine every item-NNNNNN.json from an OpenSERP batch run into one JSON."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from search import SCHEMA, atomic_json


def merge_run(directory: Path, allow_partial: bool = False) -> dict:
    manifest_file = directory / "manifest.json"
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError("manifest.json not found; provide a batch run directory") from exc
    if manifest.get("schema") != SCHEMA or not isinstance(manifest.get("items"), list):
        raise ValueError("unsupported or malformed batch manifest")

    collected, missing, engine_counts, engine_failures = [], [], Counter(), Counter()
    error_items = partial_items = 0
    for expected in manifest["items"]:
        number = expected.get("index")
        filename = f"item-{number:06d}.json" if type(number) is int and number > 0 else ""
        if filename != expected.get("file"):
            raise ValueError("unsafe or malformed manifest entry")
        path = directory / filename
        if not path.is_file():
            missing.append(filename)
            continue
        try:
            response = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{filename}: invalid JSON: {exc}") from exc
        context = response.get("_batch") if isinstance(response, dict) else None
        if (not isinstance(response, dict) or not isinstance(response.get("results"), list)
                or not isinstance(context, dict) or context.get("index") != number
                or context.get("input") != expected.get("input")):
            raise ValueError(f"{filename}: inconsistent or malformed result")
        meta = response.get("meta")
        if meta is not None and not isinstance(meta, dict):
            raise ValueError(f"{filename}: invalid metadata")
        errors = (meta or {}).get("engines_failed", [])
        if not isinstance(errors, list):
            raise ValueError(f"{filename}: invalid engines_failed")
        engine_failures.update(str(name) for name in errors)
        for result in response["results"]:
            if isinstance(result, dict):
                engine_counts[str(result.get("engine") or "unknown")] += 1
        is_error = bool(response.get("batch_error"))
        if is_error:
            error_items += 1
        elif errors:
            partial_items += 1
        collected.append({"index": number, "input": expected.get("input"),
                          "file": filename, "status": "error" if is_error else "partial" if errors else "ok",
                          "response": response})
    if missing and not allow_partial:
        raise ValueError(f"{len(missing)} JSON file(s) missing: {', '.join(missing[:5])}. Use --allow-partial to merge completed files")
    return {"schema": "openserp.batch-merged.v1",
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "run": {"created_at": manifest.get("created_at"), "source_csv": manifest.get("source_csv"),
                    "settings": manifest.get("settings", {})},
            "summary": {"planned_queries": len(manifest["items"]), "included_queries": len(collected),
                        "missing_files": missing, "failed_queries": error_items,
                        "partial_queries": partial_items,
                        "total_results": sum(engine_counts.values()),
                        "results_by_engine": dict(sorted(engine_counts.items())),
                        "failures_by_engine": dict(sorted(engine_failures.items()))},
            "items": collected}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="batch run directory containing manifest.json")
    parser.add_argument("--output", type=Path, help="output file (default: RUN_DIR/merged.json)")
    parser.add_argument("--allow-partial", action="store_true", help="merge finished files after interruption")
    parser.add_argument("--overwrite", action="store_true", help="replace an existing merged output file")
    args = parser.parse_args(argv)
    directory = args.run_dir.expanduser().resolve()
    destination = (args.output or directory / "merged.json").expanduser().resolve()
    if destination.parent != directory and directory in destination.parents:
        raise ValueError("place output in the run directory or outside it; do not create a nested output directory")
    try:
        data = merge_run(directory, args.allow_partial)
        if destination.name.startswith("item-") and destination.suffix == ".json":
            raise ValueError("output must not overwrite item JSON files")
        if destination.exists() and not args.overwrite:
            raise ValueError(f"output exists: {destination}; use --overwrite to replace it")
        destination.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(destination, data)
        print(f"Merged {data['summary']['included_queries']} inputs / {data['summary']['total_results']} results into {destination}")
        if data["summary"]["missing_files"]:
            print(f"Warning: {len(data['summary']['missing_files'])} files missing", file=sys.stderr)
        return 0
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
