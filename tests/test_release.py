from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.json"
SOURCE_REVISION = "fb2b0d4a04a165f9d32bcc2eb4a3d2d85da975f6"
EXPECTED_BOOK_STATES = [
    (1, "completed", ["github", "author.today"]),
    (2, "completed", ["github", "author.today"]),
    (3, "completed", ["github", "author.today"]),
    (4, "work_in_progress", ["github"]),
]


class ReaderReleaseTests(unittest.TestCase):
    def load_manifest(self) -> dict:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_release_contains_three_completed_books_and_open_fourth_work(self) -> None:
        data = self.load_manifest()

        self.assertEqual(data["release"], "reader-release-2")
        self.assertEqual(data["source_revision"], SOURCE_REVISION)
        self.assertRegex(data["source_revision"], r"^[0-9a-f]{40}$")
        self.assertEqual(len(data["books"]), 4)
        self.assertEqual(
            [
                (book["number"], book["status"], book["availability"])
                for book in data["books"]
            ],
            EXPECTED_BOOK_STATES,
        )
        self.assertEqual(sum("fb2" in book for book in data["books"]), 3)

        completed = [book for book in data["books"] if book["status"] == "completed"]
        in_progress = [book for book in data["books"] if book["status"] == "work_in_progress"]

        self.assertEqual([book["number"] for book in completed], [1, 2, 3])
        self.assertEqual([book["number"] for book in in_progress], [4])
        self.assertEqual(in_progress[0]["title"], "Нулевая точка")
        self.assertEqual(in_progress[0]["subtitle"], "Слово, которое вышло из текста")

        for book in completed:
            with self.subTest(book=book["number"]):
                self.assertTrue((ROOT / book["markdown"]).is_file())
                self.assertTrue((ROOT / book["fb2"]).is_file())

        self.assertTrue((ROOT / in_progress[0]["markdown"]).is_file())
        self.assertNotIn("fb2", in_progress[0])
        self.assertNotIn("author.today", in_progress[0]["availability"])

    def test_manifest_boundary_describes_the_same_release(self) -> None:
        data = self.load_manifest()
        boundary = data["boundary"]

        self.assertIn("books 1-3 are completed editions", boundary)
        self.assertIn("Author.Today", boundary)
        self.assertIn("book 4 is an open work in progress", boundary)
        self.assertIn("text may change", boundary)
        self.assertNotIn("four completed", boundary.lower())

    def test_manifest_hashes_every_reader_asset(self) -> None:
        data = self.load_manifest()
        declared = {entry["path"]: entry for entry in data["files"]}
        actual = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "books").rglob("*")
            if path.is_file()
        }

        self.assertEqual(len(declared), len(data["files"]), "manifest contains duplicate paths")
        self.assertEqual(set(declared), actual)
        for relative, entry in declared.items():
            with self.subTest(path=relative):
                self.assertFalse(relative.startswith("/"))
                self.assertNotIn("\\", relative)
                self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
                payload = (ROOT / relative).read_bytes()
                self.assertEqual(entry["size"], len(payload))
                self.assertEqual(entry["sha256"], hashlib.sha256(payload).hexdigest())

    def test_public_reader_surface_preserves_book_statuses(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
        surface = readme + "\n" + llms

        for marker in (
            "Четыре книги Джарвиса",
            "Первые три книги завершены",
            "Author.Today",
            "Работа над четвёртой книгой не окончена",
            "Нулевая точка",
            "Слово, которое вышло из текста",
            "работа не окончена",
            "текст может меняться",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, surface)

        self.assertNotIn("Книг в публичной книжной линии: 3", llms)
        self.assertNotIn("три книги Джарвиса", readme)
        self.assertNotIn("завершённым изданием", llms.split("## Статус источников", 1)[0])
        self.assertNotIn("C:\\Jarvis", surface)


if __name__ == "__main__":
    unittest.main()
