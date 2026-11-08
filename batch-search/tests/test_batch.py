"""Deterministic local HTTP tests; no external OpenSERP or browser required."""

import csv
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import search  # noqa: E402
import merge  # noqa: E402


class FakeOpenSERP(BaseHTTPRequestHandler):
    hits = []

    def do_GET(self):
        parts = urlparse(self.path)
        params = parse_qs(parts.query)
        FakeOpenSERP.hits.append((parts.path, params))
        if params["text"][0] == "network-error video 1080p full length 15 minutes":
            status, payload = 502, {"error": "all_engines_failed", "message": "all engines unavailable"}
        else:
            status = 200
            payload = {
                "query": {"text": params["text"][0], "engines_requested": params["engines"][0].split(",")},
                "meta": {"engines_responded": ["google", "bing"], "engines_failed": ["yandex"],
                         "engine_errors": [{"engine": "yandex", "error": "captcha_detected"}], "took_ms": 10},
                "results": [{"engine": "google", "title": "One", "url": "https://example.com/a"},
                            {"engine": "bing", "title": "One", "url": "https://example.com/a"}],
                "pagination": {"has_more": False},
            }
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


class BatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        FakeOpenSERP.hits = []
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeOpenSERP)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.csv_file = self.root / "keywords.csv"
        self.run_dir = self.root / "run"
        FakeOpenSERP.hits.clear()

    def args(self, **kwargs):
        args = search.parse_args([str(self.csv_file), "--api", self.url,
                                  "--output-dir", str(self.run_dir), "--delay", "0",
                                  "--retries", "0"])
        for key, value in kwargs.items():
            setattr(args, key, value)
        return args

    def test_video_batch_and_merge_preserve_duplicates_and_errors(self):
        with self.csv_file.open("w", encoding="utf-8-sig", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(["query"])
            writer.writerow(["Python آموزش"])
            writer.writerow(["Kubernetes, Docker"])
            writer.writerow(["network-error"])
        args = self.args(header=True)
        result = search.run(args)
        self.assertEqual(result, 1)
        self.assertTrue(self.run_dir.joinpath("manifest.json").exists())
        self.assertEqual(len(FakeOpenSERP.hits), 3)
        for route, params in FakeOpenSERP.hits:
            self.assertEqual(route, "/mega/search")
            self.assertEqual(params["mode"], ["balanced"])
            self.assertEqual(params["limit"], ["100"])
            self.assertEqual(params["dedupe"], ["false"])
            self.assertEqual(params["merge"], ["true"])
            self.assertEqual(params["engines"], [",".join(search.ENGINES)])
            self.assertIn("1080p", params["text"][0])
            self.assertIn("15 minutes", params["text"][0])
        self.assertIn("Kubernetes, Docker", self.run_dir.joinpath("item-000002.json").read_text())
        combined = merge.merge_run(self.run_dir)
        self.assertEqual(combined["summary"]["planned_queries"], 3)
        self.assertEqual(combined["summary"]["included_queries"], 3)
        self.assertEqual(combined["summary"]["failed_queries"], 1)
        self.assertEqual(combined["summary"]["partial_queries"], 2)
        self.assertEqual(combined["summary"]["total_results"], 4)
        self.assertEqual(combined["summary"]["results_by_engine"], {"bing": 2, "google": 2})
        self.assertEqual(combined["summary"]["failures_by_engine"], {"yandex": 2})
        self.assertEqual(combined["items"][0]["response"]["results"][0]["url"], "https://example.com/a")
        self.assertIn("batch_error", combined["items"][2]["response"])
        self.assertEqual(merge.main([str(self.run_dir)]), 0)
        self.assertTrue(self.run_dir.joinpath("merged.json").exists())

    def test_text_does_not_add_video_terms(self):
        self.csv_file.write_text("A simple query\n", encoding="utf-8")
        self.assertEqual(search.run(self.args(type="text", engines="google,bing", limit=25)), 0)
        route, params = FakeOpenSERP.hits[0]
        self.assertEqual(route, "/mega/search")
        self.assertEqual(params["text"], ["A simple query"])
        self.assertEqual(params["limit"], ["25"])
        self.assertEqual(params["engines"], ["google,bing"])
        self.assertEqual(merge.merge_run(self.run_dir)["summary"]["included_queries"], 1)

    def test_image_uses_correct_endpoint(self):
        self.csv_file.write_text("cat images\n", encoding="utf-8")
        self.assertEqual(search.run(self.args(type="image")), 0)
        self.assertEqual(FakeOpenSERP.hits[0][0], "/mega/image")
        self.assertEqual(FakeOpenSERP.hits[0][1]["text"], ["cat images"])

    def test_missing_file_is_not_silently_ignored(self):
        self.csv_file.write_text("first\nsecond\n", encoding="utf-8")
        self.assertEqual(search.run(self.args()), 0)
        self.run_dir.joinpath("item-000002.json").unlink()
        with self.assertRaisesRegex(ValueError, "missing"):
            merge.merge_run(self.run_dir)
        partial = merge.merge_run(self.run_dir, allow_partial=True)
        self.assertEqual(partial["summary"]["missing_files"], ["item-000002.json"])
        self.assertEqual(partial["summary"]["included_queries"], 1)

    def test_reject_inconsistent_results_or_unsafe_manifest(self):
        self.csv_file.write_text("first\n", encoding="utf-8")
        self.assertEqual(search.run(self.args()), 0)
        target = self.run_dir / "item-000001.json"
        data = json.loads(target.read_text())
        data["_batch"]["index"] = 99
        target.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            merge.merge_run(self.run_dir)
        data = json.loads((self.run_dir / "manifest.json").read_text())
        data["items"][0]["file"] = "../../secrets.json"
        (self.run_dir / "manifest.json").write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "unsafe"):
            merge.merge_run(self.run_dir)

    def test_csv_validation_and_overwrite_protection(self):
        self.csv_file.write_text("not,quoted\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "quote"):
            search.read_queries(self.csv_file)
        self.csv_file.write_text("valid\n", encoding="utf-8")
        self.assertEqual(search.run(self.args()), 0)
        with self.assertRaises(FileExistsError):
            search.run(self.args())
        with self.assertRaises(ValueError):
            search.parse_engines("google,not-engine")
        with self.assertRaises(ValueError):
            search.validate_api("https://user:secret@host.example:7000")


if __name__ == "__main__":
    unittest.main()
