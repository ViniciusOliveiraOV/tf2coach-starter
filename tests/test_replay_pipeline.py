"""Contrato do catálogo local: associações explícitas e saída pública sem identidades."""

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from scripts.replay_pipeline import make_server, register_replay, sync_replays, unpair_replay


FIXTURE = Path(__file__).parent / "fixtures/anonymized_demo_summary.json"


class ReplayPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "data/demos").mkdir(parents=True)
        (self.root / "data/parsed").mkdir(parents=True)
        (self.root / "dist").mkdir()
        (self.root / "dist/index.html").write_text(
            "<html><body><main>TF2 Coach</main></body></html>", encoding="utf-8"
        )
        self.stem = "2025-01-02_03-04-05"
        self.demo = self.root / "data/demos" / f"{self.stem}.dem"
        self.demo.write_bytes(b"small anonymous demo fixture")
        (self.root / "data/parsed" / f"{self.stem}.json").write_bytes(FIXTURE.read_bytes())
        self.video = self.root / "recordings/clip.mp4"
        self.video.parent.mkdir()
        self.video.write_bytes(b"0123456789")

    def test_register_pairs_explicit_video_and_keeps_private_data_out_of_api(self):
        record = register_replay(self.root, self.demo, self.video)
        self.assertEqual(record["date"], "02/01/25")
        self.assertEqual(record["report"]["metrics"]["kills"], 2)
        self.assertEqual(record["report"]["metrics"]["deaths"], 2)
        self.assertEqual(record["report"]["selection"], "POV do cabeçalho, correspondência única")
        self.assertTrue((self.root / "data/reports" / f"{self.stem}.md").exists())

        server = make_server(self.root, port=0, auto_sync=False)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            with urlopen(f"{base}/api/replays") as response:
                payload = response.read().decode("utf-8")
                self.assertEqual(response.status, 200)
            public = json.loads(payload)["replays"]
            self.assertEqual(public[0]["videoUrl"], f"/api/replays/{self.stem}/video")
            self.assertNotIn(str(self.video), payload)
            self.assertNotIn("PRIVATE_CHAT_MUST_NOT_APPEAR", payload)
            self.assertNotIn("ANON_STEAM", payload)
            self.assertNotIn("THIRD_PARTY", payload)

            with urlopen(base + "/") as response:
                page = response.read().decode("utf-8")
            self.assertIn('id="tf2coach-initial-catalog"', page)
            self.assertIn('"kills": 2', page)
            self.assertNotIn("PRIVATE_CHAT_MUST_NOT_APPEAR", page)
            self.assertNotIn("ANON_STEAM", page)
            self.assertNotIn(str(self.video), page)

            request = Request(base + public[0]["videoUrl"], headers={"Range": "bytes=2-5"})
            with urlopen(request) as response:
                self.assertEqual(response.status, 206)
                self.assertEqual(response.headers["Content-Range"], "bytes 2-5/10")
                self.assertEqual(response.read(), b"2345")

            unpair_replay(self.root, self.demo)
            with urlopen(f"{base}/api/replays") as response:
                self.assertIsNone(json.load(response)["replays"][0]["videoUrl"])
            with self.assertRaises(HTTPError) as missing:
                urlopen(base + public[0]["videoUrl"])
            self.assertEqual(missing.exception.code, 404)
            missing.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_sync_processes_new_demo_and_same_stem_video_once(self):
        same_stem_video = self.root / "data/videos" / f"{self.stem}.mp4"
        same_stem_video.parent.mkdir()
        same_stem_video.write_bytes(b"video")
        self.assertEqual(sync_replays(self.root), [self.stem])
        self.assertEqual(sync_replays(self.root), [])
        record = json.loads((self.root / "data/replays" / f"{self.stem}.json").read_text())
        self.assertEqual(record["video_path"], str(same_stem_video.resolve()))


if __name__ == "__main__":
    unittest.main()
