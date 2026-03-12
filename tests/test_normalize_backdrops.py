import tempfile
import unittest
from pathlib import Path


class NormalizeBackdropsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.album = self.root / "Artist" / "Album"
        self.album.mkdir(parents=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_plan_for_folder_reorders_backdrops_into_sequential_names(self):
        import normalize_backdrops as script

        files = [
            self.album / "backdrop3.jpg",
            self.album / "backdrop.jpg",
            self.album / "backdrop5.jpg",
        ]
        for path in files:
            path.write_text("img", encoding="utf-8")

        plan = script.plan_for_folder(self.album, files)

        self.assertEqual(
            [(source.name, target.name) for source, target in plan],
            [("backdrop3.jpg", "backdrop1.jpg"), ("backdrop5.jpg", "backdrop2.jpg")],
        )

    def test_execute_plan_applies_renames(self):
        import normalize_backdrops as script

        backdrop = self.album / "backdrop.jpg"
        backdrop_three = self.album / "backdrop3.jpg"
        backdrop.write_text("one", encoding="utf-8")
        backdrop_three.write_text("three", encoding="utf-8")

        plan = script.plan_for_folder(self.album, [backdrop, backdrop_three])
        script.execute_plan(plan)

        self.assertTrue((self.album / "backdrop.jpg").exists())
        self.assertTrue((self.album / "backdrop1.jpg").exists())
        self.assertFalse(backdrop_three.exists())


if __name__ == "__main__":
    unittest.main()
