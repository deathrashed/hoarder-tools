import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class MissingEmbeddedLyricsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.album = self.root / "Artist" / "Album"
        self.album.mkdir(parents=True)

        self.missing_track = self.album / "01 Missing.mp3"
        self.embedded_track = self.album / "02 Embedded.flac"

        self.missing_track.write_text("x", encoding="utf-8")
        self.embedded_track.write_text("x", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_writes_only_missing_tracks_to_list_file(self):
        import lyrics_find_missing_embedded as script

        def fake_has_embedded(audio_path):
            return audio_path.endswith("02 Embedded.flac")

        with patch.object(script, "has_embedded_lyrics", side_effect=fake_has_embedded):
            report = script.scan_archive_for_missing_embedded_lyrics(str(self.root))

        output_path = self.root / "missing_embedded_lyrics.txt"
        script.write_track_list(report["matches"], str(output_path))

        self.assertEqual(output_path.read_text(encoding="utf-8").splitlines(), [str(self.missing_track)])
        self.assertEqual(report["total_audio_files"], 2)
        self.assertEqual(report["missing_embedded_lyrics"], 1)

    def test_can_open_written_track_list_in_lyrics_finder(self):
        import lyrics_find_missing_embedded as script

        output_path = self.root / "missing_embedded_lyrics.txt"
        script.write_track_list([str(self.missing_track)], str(output_path))

        with patch.object(script, "open_track_list_in_lyrics_finder") as mocked_open:
            script.maybe_open_track_list(str(output_path), should_open=True)

        mocked_open.assert_called_once_with(str(output_path))

    def test_can_prompt_after_scan_to_open_in_lyrics_finder(self):
        import lyrics_find_missing_embedded as script

        output_path = self.root / "missing_embedded_lyrics.txt"
        script.write_track_list([str(self.missing_track)], str(output_path))

        with patch.object(script.Confirm, "ask", return_value=True) as mocked_confirm, patch.object(
            script, "open_track_list_in_lyrics_finder"
        ) as mocked_open:
            script.maybe_prompt_open_track_list(str(output_path), should_prompt=True)

        mocked_confirm.assert_called_once()
        mocked_open.assert_called_once_with(str(output_path))


if __name__ == "__main__":
    unittest.main()
