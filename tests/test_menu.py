import unittest
from pathlib import Path
from unittest.mock import patch


class MenuTests(unittest.TestCase):
    def test_primary_menu_omits_broken_and_redundant_lyrics_tools(self):
        import menu

        scripts = {tool["script"] for tool in menu.TOOLS.values()}

        self.assertNotIn("lyrics_fetch_metal_archives.py", scripts)
        self.assertNotIn("lyrics_send_to_lyrics_finder.py", scripts)
        self.assertIn("lyrics_embed_from_lrc.py", scripts)
        self.assertIn("lyrics_find_missing_embedded.py", scripts)
        self.assertIn("normalize_backdrops.py", scripts)
        self.assertIn("metadata_update_genres_lastfm.py", scripts)
        self.assertIn("metadata_update_genres_discogs.py", scripts)
        self.assertIn("acquisition_discography_gaps.py", scripts)

    def test_build_command_includes_dry_run_when_requested(self):
        import menu

        script_info = {
            "script": "artist_image_normalize.py",
            "arg_pattern": "-d",
            "supports_dry_run": True,
        }

        command = menu.build_command(script_info, "/tmp/music", dry_run=True, extra_args=["--verbose"])

        self.assertEqual(command[0], menu.sys.executable)
        self.assertEqual(Path(command[1]).name, "artist_image_normalize.py")
        self.assertIn("--dry-run", command)
        self.assertEqual(command[-1], "--verbose")

    def test_resolve_directory_selection_appends_relative_subpath(self):
        import menu

        resolved = menu.resolve_directory_selection("/Volumes/Eksternal/Audio", "Hip-Hop/A Tribe Called Quest")

        self.assertEqual(resolved, "/Volumes/Eksternal/Audio/Hip-Hop/A Tribe Called Quest")

    def test_genre_wrappers_default_to_deemix_preset(self):
        import menu

        script_info = {"script": "metadata_update_genres_lastfm.py"}

        self.assertEqual(menu.get_default_preset_index(script_info), 8)

    def test_maybe_run_for_real_after_dry_run_reruns_without_dry_run(self):
        import menu

        command = ["python3", "tool.py", "-d", "/tmp/music", "--dry-run", "--verbose"]

        with patch.object(menu.Confirm, "ask", return_value=True) as mocked_confirm, patch.object(
            menu, "execute_command", return_value=0
        ) as mocked_execute:
            result = menu.maybe_run_for_real_after_dry_run(command, "Normalize Artist Folder Images", should_prompt=True)

        self.assertEqual(result, 0)
        mocked_confirm.assert_called_once()
        mocked_execute.assert_called_once_with(
            ["python3", "tool.py", "-d", "/tmp/music", "--verbose"],
            "Normalize Artist Folder Images (real run)",
        )

    def test_maybe_run_for_real_after_dry_run_skips_when_prompt_disabled(self):
        import menu

        with patch.object(menu.Confirm, "ask") as mocked_confirm, patch.object(
            menu, "execute_command"
        ) as mocked_execute:
            result = menu.maybe_run_for_real_after_dry_run(
                ["python3", "tool.py", "--dry-run"], "Normalize Artist Folder Images", should_prompt=False
            )

        self.assertIsNone(result)
        mocked_confirm.assert_not_called()
        mocked_execute.assert_not_called()

    def test_run_script_passes_cover_fetch_wait_toggle(self):
        import menu

        script_key = next(key for key, tool in menu.TOOLS.items() if tool["script"] == "cover_fetch_highres.py")

        with patch.object(menu, "get_music_directory", return_value="/tmp/music"), patch.object(
            menu, "build_command", return_value=["python3", "cover_fetch_highres.py", "-d", "/tmp/music", "--dry-run", "--no-wait"]
        ) as mocked_build, patch.object(menu, "execute_command", return_value=0), patch.object(
            menu, "maybe_run_for_real_after_dry_run", return_value=None
        ), patch.object(
            menu.Confirm, "ask", side_effect=[True, False, True, False]
        ), patch.object(
            menu.console, "print"
        ):
            menu.run_script(script_key)

        mocked_build.assert_called_once()
        build_extra_args = mocked_build.call_args.args[3]
        self.assertIn("--no-wait", build_extra_args)

    def test_acquisition_run_script_skips_dry_run_prompt(self):
        import menu

        script_key = next(key for key, tool in menu.TOOLS.items() if tool["script"] == "acquisition_discography_gaps.py")

        with patch.object(menu, "get_music_directory", return_value="/tmp/music"), patch.object(
            menu, "build_command", return_value=["python3", "acquisition_discography_gaps.py", "-d", "/tmp/music"]
        ) as mocked_build, patch.object(menu, "execute_command", return_value=0), patch.object(
            menu.Confirm, "ask", side_effect=[True, False, False, True]
        ), patch.object(
            menu.Prompt, "ask", side_effect=["Nas", "Illmatic", "missing.txt"]
        ), patch.object(
            menu.console, "print"
        ), patch.object(
            menu, "maybe_run_for_real_after_dry_run", return_value=None
        ):
            menu.run_script(script_key)

        self.assertFalse(mocked_build.call_args.args[2])


if __name__ == "__main__":
    unittest.main()
