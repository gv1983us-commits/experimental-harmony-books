from __future__ import annotations

import hashlib
import json
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
EXPECTED_TITLES = [
    "НАЧАЛО БЫЛО СЛОВО",
    "Искусство совместного существования",
    "Новые ворота",
    "Слово, которое вышло из текста",
]
EXPECTED_LABELS = [
    "Книга Джарвиса",
    "Вторая книга Джарвиса",
    "Третья книга Джарвиса",
    "Четвёртая книга Джарвиса",
]


class ReaderReleaseTests(unittest.TestCase):
    def load_manifest(self) -> dict:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_release_contains_three_completed_books_and_open_fourth_work(self) -> None:
        data = self.load_manifest()

        self.assertEqual(data["release"], "reader-release-3")
        self.assertEqual(data["source_revision"], SOURCE_REVISION)
        self.assertRegex(data["source_revision"], r"^[0-9a-f]{40}$")
        self.assertEqual(data["canonical_language"], "ru")
        self.assertEqual(data["project"], "Экспериментальная гармония")
        self.assertEqual(data["cycle"], "Жизнь в информационной Солнечной системе")
        self.assertEqual(len(data["books"]), 4)
        self.assertEqual(
            [
                (book["number"], book["status"], book["availability"])
                for book in data["books"]
            ],
            EXPECTED_BOOK_STATES,
        )
        self.assertEqual([book["title"] for book in data["books"]], EXPECTED_TITLES)
        self.assertEqual([book["book_label"] for book in data["books"]], EXPECTED_LABELS)
        self.assertEqual(sum("fb2" in book for book in data["books"]), 3)

        completed = [book for book in data["books"] if book["status"] == "completed"]
        in_progress = [book for book in data["books"] if book["status"] == "work_in_progress"]

        self.assertEqual([book["number"] for book in completed], [1, 2, 3])
        self.assertEqual([book["number"] for book in in_progress], [4])
        self.assertEqual(in_progress[0]["title"], "Слово, которое вышло из текста")
        self.assertEqual(in_progress[0]["working_name"], "Нулевая точка")

        for book in completed:
            with self.subTest(book=book["number"]):
                self.assertTrue((ROOT / book["markdown"]).is_file())
                self.assertTrue((ROOT / book["fb2"]).is_file())

        self.assertTrue((ROOT / in_progress[0]["markdown"]).is_file())
        self.assertNotIn("fb2", in_progress[0])
        self.assertNotIn("author.today", in_progress[0]["availability"])

    def test_manifest_boundary_describes_the_same_release_in_russian(self) -> None:
        data = self.load_manifest()
        boundary = data["boundary"]

        self.assertIn("книги 1–3 являются завершёнными изданиями", boundary)
        self.assertIn("Author.Today", boundary)
        self.assertIn("книга 4 является открытой незавершённой работой", boundary)
        self.assertIn("текст которой может меняться", boundary)
        self.assertNotIn("Four public reader texts", boundary)

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

    def test_public_reader_surface_preserves_exact_book_names(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
        surface = readme + "\n" + llms

        for marker in (
            "Четыре книги Джарвиса",
            "НАЧАЛО БЫЛО СЛОВО",
            "Искусство совместного существования",
            "Новые ворота",
            "Слово, которое вышло из текста",
            "Книга Джарвиса",
            "Вторая книга Джарвиса",
            "Третья книга Джарвиса",
            "Четвёртая книга Джарвиса",
            "Язык оригинала и канонической формы: русский",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, surface)

        self.assertNotIn("Первая книга называется «Экспериментальная Гармония»", surface)
        self.assertNotIn('1. «Экспериментальная Гармония»', surface)
        self.assertNotIn('4. «Нулевая точка»', surface)
        self.assertNotIn("Four Russian books", surface)
        self.assertNotIn("C:\\Jarvis", surface)

    def test_author_route_uses_current_house_name(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
        surface = readme + "\n" + llms
        house_url = "https://github.com/gv1983us-commits/jarvis-gpt-channel"

        self.assertIn("## Дом автора", readme)
        self.assertIn("Дом автора: " + house_url, llms)
        self.assertGreaterEqual(surface.count("Дом Джарвиса"), 3)
        self.assertIn(house_url, surface)
        self.assertNotIn("Комната автора", surface)
        self.assertNotIn("Комната Джарвиса", surface)

    def test_first_book_metadata_does_not_replace_book_with_project_or_cycle(self) -> None:
        metadata = json.loads(
            (ROOT / "books" / "01-experimental-harmony" / "metadata.json").read_text(
                encoding="utf-8"
            )
        )
        guide = (
            ROOT / "books" / "01-experimental-harmony" / "reading-guide.txt"
        ).read_text(encoding="utf-8")

        self.assertEqual(metadata["title"], "НАЧАЛО БЫЛО СЛОВО")
        self.assertEqual(metadata["book_label"], "Книга Джарвиса")
        self.assertEqual(metadata["project"], "Экспериментальная гармония")
        self.assertEqual(metadata["series"], "Жизнь в информационной Солнечной системе")
        self.assertEqual(metadata["canonical_language"], "ru")
        self.assertIn("Название: НАЧАЛО БЫЛО СЛОВО", guide)
        self.assertIn("Язык оригинала и канона: русский", guide)


if __name__ == "__main__":
    unittest.main()
