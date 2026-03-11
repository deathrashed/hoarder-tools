import tempfile
import unittest
from pathlib import Path


class ArtistImageNormalizeTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_renames_folder_jpg_to_artist_jpg_when_artist_image_missing(self):
        import artist_image_normalize as script

        artist_dir = self.root / "A" / "Artist"
        artist_dir.mkdir(parents=True)
        folder_image = artist_dir / "folder.jpg"
        folder_image.write_text("folder", encoding="utf-8")

        result = script.normalize_artist_image_folder(artist_dir, dry_run=False)

        self.assertEqual(result, "renamed")
        self.assertFalse(folder_image.exists())
        self.assertTrue((artist_dir / "artist.jpg").exists())

    def test_deletes_folder_jpg_when_artist_jpg_already_exists(self):
        import artist_image_normalize as script

        artist_dir = self.root / "A" / "Artist"
        artist_dir.mkdir(parents=True)
        folder_image = artist_dir / "folder.jpg"
        artist_image = artist_dir / "artist.jpg"
        folder_image.write_text("folder", encoding="utf-8")
        artist_image.write_text("artist", encoding="utf-8")

        result = script.normalize_artist_image_folder(artist_dir, dry_run=False)

        self.assertEqual(result, "deleted_duplicate")
        self.assertFalse(folder_image.exists())
        self.assertTrue(artist_image.exists())


if __name__ == "__main__":
    unittest.main()
