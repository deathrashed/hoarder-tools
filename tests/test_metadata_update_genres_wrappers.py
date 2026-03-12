import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class GenreWrapperTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.album = self.root / "Artist" / "Album"
        self.album.mkdir(parents=True)
        self.track = self.album / "01 Track.mp3"
        self.track.write_text("audio", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_lastfm_dry_run_groups_by_artist(self):
        import metadata_update_genres_lastfm as script

        with patch.object(script, "read_artist", return_value="Artist"):
            _, artist_map, missing = script.build_artist_map(self.root)

        self.assertEqual(list(artist_map.keys()), ["Artist"])
        self.assertEqual(artist_map["Artist"], [self.track])
        self.assertEqual(missing, [])

    def test_discogs_dry_run_groups_by_artist_and_album(self):
        import metadata_update_genres_discogs as script

        with patch.object(script, "read_artist_album", return_value=("Artist", "Album")):
            _, album_map, missing = script.build_album_map(self.root)

        self.assertEqual(list(album_map.keys()), [("Artist", "Album")])
        self.assertEqual(album_map[("Artist", "Album")], [self.track])
        self.assertEqual(missing, [])

    def test_lastfm_runtime_validation_requires_env_and_node(self):
        import metadata_update_genres_lastfm as script

        with patch.dict(os.environ, {}, clear=True), patch.object(script, "SCRIPT_PATH", Path("/tmp/missing.js")), patch(
            "metadata_update_genres_lastfm.shutil.which", return_value=None
        ):
            problems = script.validate_runtime()

        self.assertTrue(any("LASTFM_API_KEY" in problem for problem in problems))
        self.assertTrue(any("node" in problem for problem in problems))

    def test_discogs_runtime_validation_requires_env_and_node(self):
        import metadata_update_genres_discogs as script

        with patch.dict(os.environ, {}, clear=True), patch.object(script, "SCRIPT_PATH", Path("/tmp/missing.js")), patch(
            "metadata_update_genres_discogs.shutil.which", return_value=None
        ):
            problems = script.validate_runtime()

        self.assertTrue(any("DISCOGS_API_TOKEN" in problem for problem in problems))
        self.assertTrue(any("node" in problem for problem in problems))


if __name__ == "__main__":
    unittest.main()
