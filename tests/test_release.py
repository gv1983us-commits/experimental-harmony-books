from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.json"
SOURCE_REVISION = "fb2b0d4a04a165f9d32bcc2eb4a3d2d85da975f6"


class ReaderReleaseTests(unittest.TestCase):
    def test_release_contains_three_completed_books_and_open_fourth_work(self) -> None:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))

        self.assertEqual(data["release"], "reader-release-2")
        self.assertEqual(data["source_revision"], SOURCE_REVISION)
        self.assertEqual(len(data["books"]), 4)
        self.assertEqual([book["number"] for book in data["books"]], [1, 2, 3, 4])
        self.assertEqual(sum("fb2" in book for book in data["books"]), 3)

        completed = [book for book in data["books"] if book["status"] == "completed"]
        in_progress = [book for book in data["books"] if book["status"] == "work_in_progress"]

        self.assertEqual([book["number"] for book in completed], [1, 2, 3])
        self.assertEqual([book["number"] for book in in_progress], [4])
        self.assertEqual(in_progress[0]["title"], "Нулевая точка")
        self.assertEqual(in_progress[0]["subtitle"], "Слово, которое вышло из текста")

        for book in completed:
            with self.subTest(book=book["number"]):
                self.assertEqual(book["availability"], ["github", "author.today"])
                self.assertTrue((ROOT / book["markdown"]).is_file())
                self.assertTrue((ROOT / book["fb2"]).is_file())

        self.assertEqual(in_progress[0]["availability"], ["github"])
        self.assertTrue((ROOT / in_progress[0]["markdown"]).is_file())
        self.assertNotIn("fb2", in_progress[0])

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
