import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class LyricsFinderQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.album = self.root / "Artist" / "Album"
        self.album.mkdir(parents=True)

        self.missing_track = self.album / "01 Missing.mp3"
        self.sidecar_track = self.album / "02 Has LRC.mp3"
        self.embedded_track = self.album / "03 Embedded.flac"
        self.non_audio = self.album / "notes.txt"

        for path in [self.missing_track, self.sidecar_track, self.embedded_track, self.non_audio]:
            path.write_text("x", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_collects_only_tracks_missing_embedded_and_sidecar_lyrics(self):
        import lyrics_send_to_lyrics_finder as script

        def fake_has_embedded(audio_path):
            return audio_path.endswith("03 Embedded.flac")

        def fake_find_lrc(audio_path):
            if audio_path.endswith("02 Has LRC.mp3"):
                return str(self.album / "02 Has LRC.lrc")
            return None

        with patch.object(script, "has_embedded_lyrics", side_effect=fake_has_embedded), patch.object(
            script, "find_lrc", side_effect=fake_find_lrc
        ):
            results = script.collect_missing_lyrics_tracks(str(self.root))

        self.assertEqual(results, [str(self.missing_track)])

    def test_opens_lyrics_finder_with_exact_paths(self):
        import lyrics_send_to_lyrics_finder as script

        with patch.object(script.subprocess, "run") as mocked_run:
            script.open_in_lyrics_finder([str(self.missing_track), str(self.sidecar_track)])

        mocked_run.assert_called_once_with(
            ["/usr/bin/open", "-a", "Lyrics Finder", str(self.missing_track), str(self.sidecar_track)],
            check=True,
        )

    def test_loads_track_list_from_file(self):
        import lyrics_send_to_lyrics_finder as script

        path_list = self.root / "missing_lyrics.txt"
        path_list.write_text(
            f"{self.missing_track}\n\n{self.sidecar_track}\n",
            encoding="utf-8",
        )

        results = script.load_track_list(str(path_list))

        self.assertEqual(results, [str(self.missing_track), str(self.sidecar_track)])


if __name__ == "__main__":
    unittest.main()
