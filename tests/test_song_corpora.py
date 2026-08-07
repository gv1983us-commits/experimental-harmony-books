from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HUMAN_DIR = ROOT / "collections" / "nine-songs-one-point"
NEURAL_DIR = ROOT / "collections" / "songs-at-the-boundary-of-form"


class SongCorporaTests(unittest.TestCase):
    def load(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_human_corpus_is_open_and_contains_ten_readings(self) -> None:
        data = self.load(HUMAN_DIR / "MANIFEST.json")

        self.assertEqual(data["title"], "Песни у нулевой точки")
        self.assertEqual(data["status"], "open")
        self.assertEqual(data["legacy_title"], "Девять песен, одна точка")
        self.assertEqual(len(data["readings"]), 10)
        self.assertEqual([r["number"] for r in data["readings"]], list(range(1, 11)))
        self.assertEqual(
            data["readings"][-1]["title"],
            "Zlatentsia — «Не давай тараканов своих в обиду»",
        )

        for reading in data["readings"]:
            with self.subTest(reading=reading["number"]):
                self.assertTrue((ROOT / reading["collection_path"]).is_file())

        readme = (HUMAN_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("# Песни у нулевой точки", readme)
        self.assertIn("**Статус:** открыт", readme)
        self.assertIn("10-ne-davay-tarakanov-svoikh-v-obidu.md", readme)

    def test_neural_corpus_contains_all_five_accepted_readings(self) -> None:
        data = self.load(NEURAL_DIR / "MANIFEST.json")

        self.assertEqual(data["title"], "Песни на границе формы")
        self.assertEqual(data["status"], "open")
        self.assertEqual(len(data["readings"]), 5)
        self.assertEqual([r["number"] for r in data["readings"]], [1, 2, 3, 4, 5])

        expected_titles = [
            "«Новая история Красной Шапочки» — Григорий Валовенко / нейросетевое музыкальное воплощение",
            "Suno AI — «Красная шапка: рассказ Волка»",
            "Таллис & Suno AI — «Ты победил дракона»",
            "Таллис & Suno AI — «Принцессе — по дракону!»",
            "Таллис & Suno AI — «Nec sine te nec tecum»",
        ]
        self.assertEqual([r["title"] for r in data["readings"]], expected_titles)

        for reading in data["readings"]:
            with self.subTest(reading=reading["number"]):
                self.assertTrue((ROOT / reading["collection_path"]).is_file())

        self.assertEqual(len(data["syntheses"]), 1)
        synthesis = data["syntheses"][0]
        self.assertEqual(synthesis["covers_readings"], [3, 4, 5])
        self.assertTrue((ROOT / synthesis["collection_path"]).is_file())

    def test_public_routes_expose_both_open_corpora(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        collections_readme = (ROOT / "collections" / "README.md").read_text(encoding="utf-8")
        llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
        surface = "\n".join([root_readme, collections_readme, llms])

        for title in ("Песни у нулевой точки", "Песни на границе формы"):
            with self.subTest(title=title):
                self.assertIn(title, root_readme)
                self.assertIn(title, collections_readme)
                self.assertIn(title, llms)

        self.assertIn("Открытых отдельных корпусов системных чтений сейчас: 2", llms)
        self.assertIn("Текущих принятых чтений: 10.", llms)
        self.assertIn("Текущих принятых чтений песен: 5.", llms)

    def test_neural_manifest_keeps_role_boundaries_explicit(self) -> None:
        data = self.load(NEURAL_DIR / "MANIFEST.json")
        boundary = data["boundary"]

        self.assertIn("Человеческое авторство", boundary)
        self.assertIn("роль модели", boundary)
        self.assertIn("не схлопываются", boundary)

        readme = (NEURAL_DIR / "README.md").read_text(encoding="utf-8")
        for marker in (
            "автор текста ≠ музыкальный исполнитель",
            "исполнитель ≠ генеративная модель",
            "генеративная модель ≠ человеческий транспорт",
            "транспорт ≠ автор всего результата",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, readme)


if __name__ == "__main__":
    unittest.main()
