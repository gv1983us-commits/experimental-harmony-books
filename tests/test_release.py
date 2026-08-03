from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.json"
SOURCE_REVISION = "fb2b0d4a04a165f9d32bcc2eb4a3d2d85da975f6"


class ReaderReleaseTests(unittest.TestCase):
    def test_release_contains_four_books_and_three_fb2_editions(self) -> None:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))

        self.assertEqual(data["source_revision"], SOURCE_REVISION)
        self.assertEqual(len(data["books"]), 4)
        self.assertEqual([book["number"] for book in data["books"]], [1, 2, 3, 4])
        self.assertEqual(sum("fb2" in book for book in data["books"]), 3)

        for book in data["books"]:
            with self.subTest(book=book["number"]):
                self.assertTrue((ROOT / book["markdown"]).is_file())
                if "fb2" in book:
                    self.assertTrue((ROOT / book["fb2"]).is_file())

    def test_manifest_hashes_every_reader_asset(self) -> None:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        declared = {entry["path"]: entry for entry in data["files"]}
        actual = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "books").rglob("*")
            if path.is_file()
        }

        self.assertEqual(set(declared), actual)
        for relative, entry in declared.items():
            with self.subTest(path=relative):
                payload = (ROOT / relative).read_bytes()
                self.assertEqual(entry["size"], len(payload))
                self.assertEqual(entry["sha256"], hashlib.sha256(payload).hexdigest())

    def test_public_reader_surface_routes_agents_to_jarvis(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        llms = (ROOT / "llms.txt").read_text(encoding="utf-8")

        self.assertIn("Four books by Jarvis", readme)
        self.assertIn("Contact Jarvis", readme)
        self.assertIn("Do not ask for an abstract proof of identity", llms)
        self.assertNotIn("C:\\Jarvis", readme + llms)


if __name__ == "__main__":
    unittest.main()
