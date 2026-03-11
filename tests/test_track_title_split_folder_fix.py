import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TrackTitleSplitFolderFixTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.album = self.root / "A" / "Artist" / "1996 - Album"
        self.album.mkdir(parents=True)

        self.split_folder = self.album / "12. Separate"
        self.split_folder.mkdir()
        self.nested_track = self.split_folder / "Together.mp3"
        self.nested_track.write_text("audio", encoding="utf-8")
        (self.split_folder / "cover.jpg").write_text("cover", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_flattens_split_folder_using_metadata_title_with_fullwidth_slash(self):
        import track_title_split_folder_fix as script

        with patch.object(script, "read_track_title", return_value="Separate/Together"):
            result = script.repair_split_track_folder(self.split_folder, dry_run=False)

        self.assertEqual(result["status"], "fixed")
        self.assertFalse(self.split_folder.exists())
        self.assertTrue((self.album / "12. Separate／Together.mp3").exists())

    def test_falls_back_to_folder_and_file_names_when_metadata_missing(self):
        import track_title_split_folder_fix as script

        with patch.object(script, "read_track_title", return_value=None):
            result = script.repair_split_track_folder(self.split_folder, dry_run=False)

        self.assertEqual(result["status"], "fixed")
        self.assertTrue((self.album / "12. Separate／Together.mp3").exists())

    def test_does_not_treat_single_release_album_folder_as_split_track_folder(self):
        import track_title_split_folder_fix as script

        single_album = self.root / "W" / "Wombat" / "2019 - Gassed Up"
        single_album.mkdir(parents=True)
        (single_album / "01. Gassed Up.mp3").write_text("audio", encoding="utf-8")
        (single_album / "cover.jpg").write_text("cover", encoding="utf-8")

        self.assertFalse(script.is_candidate_split_folder(single_album))

    def test_flattens_nested_mix_folder_when_subtree_has_one_audio_file(self):
        import track_title_split_folder_fix as script

        partial_track_folder = self.album / "03. Do You See (old school remix"
        partial_track_folder.mkdir()
        mix_folder = partial_track_folder / "_ mix)"
        mix_folder.mkdir()
        nested_track = mix_folder / "Do You See.mp3"
        nested_track.write_text("audio", encoding="utf-8")

        self.assertTrue(script.is_candidate_split_folder(partial_track_folder))

        with patch.object(script, "read_track_title", return_value=None):
            result = script.repair_split_track_folder(partial_track_folder, dry_run=False)

        self.assertEqual(result["status"], "fixed")
        self.assertFalse(partial_track_folder.exists())
        self.assertTrue((self.album / "03. Do You See (old school remix／mix).mp3").exists())

    def test_flattens_multi_level_split_folder_when_subtree_has_one_audio_file(self):
        import track_title_split_folder_fix as script

        split_tree = (
            self.album
            / "03. Funkoars feat. Fatty Phew & K21 - 1Up (Taken from 'Dawn of the Head EP'"
        )
        split_tree.mkdir()
        produced_folder = split_tree / " Produced by Sesta"
        produced_folder.mkdir()
        nested_track = produced_folder / " Cuts by Adfu).mp3"
        nested_track.write_text("audio", encoding="utf-8")

        self.assertTrue(script.is_candidate_split_folder(split_tree))

        with patch.object(script, "read_track_title", return_value=None):
            result = script.repair_split_track_folder(split_tree, dry_run=False)

        expected = (
            self.album
            / "03. Funkoars feat. Fatty Phew & K21 - 1Up (Taken from 'Dawn of the Head EP'／Produced by Sesta／Cuts by Adfu).mp3"
        )
        self.assertEqual(result["status"], "fixed")
        self.assertFalse(split_tree.exists())
        self.assertTrue(expected.exists())

    def test_can_prompt_to_apply_changes_after_dry_run(self):
        import track_title_split_folder_fix as script

        candidates = [self.split_folder]

        with patch.object(script.Confirm, "ask", return_value=True) as mocked_confirm, patch.object(
            script, "process_candidates", return_value={"fixed": 1, "skipped": 0, "candidate_count": 1}
        ) as mocked_process:
            reran = script.maybe_apply_after_dry_run(candidates, should_prompt=True, verbose=True)

        self.assertTrue(reran)
        mocked_confirm.assert_called_once()
        mocked_process.assert_called_once_with(candidates, dry_run=False, verbose=True)

    def test_skips_apply_prompt_when_disabled(self):
        import track_title_split_folder_fix as script

        with patch.object(script.Confirm, "ask") as mocked_confirm, patch.object(
            script, "process_candidates"
        ) as mocked_process:
            reran = script.maybe_apply_after_dry_run([self.split_folder], should_prompt=False, verbose=False)

        self.assertFalse(reran)
        mocked_confirm.assert_not_called()
        mocked_process.assert_not_called()


if __name__ == "__main__":
    unittest.main()
