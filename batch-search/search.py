#!/usr/bin/env python3
"""Batch OpenSERP search: one UTF-8 CSV entry per line, one JSON per entry."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

ENGINES = ("google", "bing", "yandex", "baidu", "duckduckgo", "ecosia")
SCHEMA = "openserp.batch.v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_queries(path: Path, skip_header: bool = False) -> list[dict]:
    queries = []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        for row in reader:
            line = reader.line_num
            if not row or all(not cell.strip() for cell in row):
                continue
            if len(row) != 1:
                raise ValueError(f"CSV line {line}: expected one field per line; quote values containing commas")
            query = row[0].strip()
            if not query:
                continue
            if skip_header:
                skip_header = False
                continue
            queries.append({"index": len(queries) + 1, "source_line": line,
                            "input": query, "file": f"item-{len(queries) + 1:06d}.json"})
    if not queries:
        raise ValueError("CSV contains no search terms")
    return queries


def parse_engines(value: str) -> list[str]:
    names = list(dict.fromkeys(part.strip().lower() for part in value.split(",")))
    invalid = [name for name in names if name not in ENGINES]
    if invalid:
        raise ValueError(f"invalid engines: {', '.join(invalid)}; available: {', '.join(ENGINES)}")
    if not names:
        raise ValueError("select at least one search engine")
    return names


def validate_api(value: str) -> str:
    u = urlsplit(value)
    if u.scheme not in ("http", "https") or not u.netloc or u.username or u.password:
        raise ValueError("--api must be an HTTP(S) base URL without credentials")
    if u.path not in ("", "/") or u.query or u.fragment:
        raise ValueError("--api should be the origin only, e.g. http://127.0.0.1:7000")
    return f"{u.scheme}://{u.netloc}"


def search_text(query: str, kind: str, quality: str, min_minutes: int) -> str:
    if kind != "video":
        return query
    qualifiers = ["video"]
    if quality:
        qualifiers.append(quality)
    if min_minutes:
        qualifiers.extend(["full length", f"{min_minutes} minutes"])
    return " ".join([query, *qualifiers])


def request_search(api: str, params: dict[str, str | int], kind: str, timeout: float, retries: int) -> dict:
    endpoint = "/mega/image" if kind == "image" else "/mega/search"
    url = f"{api}{endpoint}?{urlencode(params)}"
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "openserp-batch-search/1.0"})
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                data = json.load(response)
            if not isinstance(data, dict) or not isinstance(data.get("results"), list):
                raise ValueError("OpenSERP response lacks a results array")
            return data
        except HTTPError as exc:
            body = exc.read(4096).decode("utf-8", errors="replace")
            try:
                parsed = json.loads(body)
                detail = parsed.get("message") or parsed.get("error") or str(exc)
            except (json.JSONDecodeError, AttributeError):
                detail = str(exc)
            if exc.code in (429, 502, 503, 504) and attempt < retries:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise RuntimeError(f"HTTP {exc.code}: {str(detail)[:400]}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            if attempt < retries:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise RuntimeError(f"network error: {exc}") from exc
    raise AssertionError("unreachable")


def atomic_json(path: Path, value: dict) -> None:
    import os
    import tempfile

    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".pending-", suffix=".json", delete=False) as out:
            tmp = Path(out.name)
            json.dump(value, out, ensure_ascii=False, indent=2)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        tmp.replace(path)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path, help="UTF-8 CSV with one search phrase per row")
    parser.add_argument("--api", default="http://127.0.0.1:7000")
    parser.add_argument("--type", choices=["video", "text", "web", "image", "all"], default="video")
    parser.add_argument("--quality", default="1080p", help="video search keyword; use '' to disable")
    parser.add_argument("--min-minutes", type=int, default=15, help="video search keyword only (default: 15)")
    parser.add_argument("--engines", default=",".join(ENGINES), help="comma-separated engines")
    parser.add_argument("--limit", type=int, default=100, help="maximum requested per engine (1..100)")
    parser.add_argument("--site", default="", help="restrict search to a domain")
    parser.add_argument("--timeout", type=float, default=150, help="request timeout in seconds")
    parser.add_argument("--retries", type=int, default=1, help="retries for temporary failures")
    parser.add_argument("--delay", type=float, default=2, help="pause between CSV rows in seconds")
    parser.add_argument("--header", action="store_true", help="skip the first nonempty CSV row")
    parser.add_argument("--output-dir", type=Path, help="new output directory; must not exist")
    args = parser.parse_args(argv)
    if not 1 <= args.limit <= 100:
        parser.error("--limit must be 1..100")
    if args.min_minutes < 0 or args.timeout <= 0 or args.delay < 0 or args.retries < 0:
        parser.error("min-minutes/delay/retries must be nonnegative and timeout positive")
    return args


def run(args: argparse.Namespace) -> int:
    api = validate_api(args.api)
    engines = parse_engines(args.engines)
    source = args.csv_file.expanduser().resolve()
    queries = read_queries(source, args.header)
    if args.site and not re.fullmatch(r"(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}", args.site):
        raise ValueError("--site must be a domain such as youtube.com")
    folder = args.output_dir or (Path(__file__).resolve().parent / "results" /
                                 (datetime.now(timezone.utc).strftime("run-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8]))
    folder = folder.expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=False)  # never overwrite an earlier batch
    manifest = {"schema": SCHEMA, "created_at": utc_now(), "source_csv": str(source),
                "settings": {"api": api, "type": args.type, "quality_keyword": args.quality,
                             "min_minutes_keyword": args.min_minutes, "engines": engines,
                             "limit_per_engine": args.limit, "site": args.site}, "items": queries}
    atomic_json(folder / "manifest.json", manifest)
    print(f"Output: {folder}", flush=True)
    failed = 0
    partial = 0
    for index, item in enumerate(queries):
        if index and args.delay:
            time.sleep(args.delay)
        text = search_text(item["input"], args.type, args.quality, args.min_minutes)
        params = {"text": text, "engines": ",".join(engines), "limit": args.limit,
                  "mode": "balanced", "dedupe": "false", "merge": "true"}
        if args.site:
            params["site"] = args.site
        context = {"index": item["index"], "source_line": item["source_line"],
                   "input": item["input"], "requested_text": text, "type": args.type,
                   "limit_per_engine": args.limit}
        try:
            data = request_search(api, params, args.type, args.timeout, args.retries)
            data["_batch"] = context
            meta = data.get("meta")
            if not isinstance(meta, dict):
                raise ValueError("OpenSERP response has invalid meta object")
            failures = meta.get("engines_failed", [])
            if not isinstance(failures, list):
                raise ValueError("OpenSERP response has invalid engines_failed list")
            if failures:
                partial += 1
            result_count = len(data["results"])
            status = f"{result_count} result(s), {len(failures)} engine failure(s)"
        except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
            failed += 1
            data = {"query": {"text": text, "engines_requested": engines},
                    "results": [], "_batch": context,
                    "batch_error": {"message": str(exc)}}
            status = f"ERROR: {exc}"
        atomic_json(folder / item["file"], data)
        print(f"[{item['index']}/{len(queries)}] {item['file']}: {status}", flush=True)
    print(f"Complete: {len(queries)} inputs, {failed} failed, {partial} partially failed.")
    print(f"Merge: python3 batch-search/merge.py {folder}")
    return 1 if failed else 0


def main() -> None:
    try:
        sys.exit(run(parse_args()))
    except (OSError, csv.Error, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("\nInterrupted. Completed JSON files remain in the output folder.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
