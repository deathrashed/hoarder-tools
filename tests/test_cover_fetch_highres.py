import tempfile
import unittest
from io import StringIO
from urllib.parse import parse_qs, urlparse
from pathlib import Path
from unittest.mock import patch


class CoverFetchHighResTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.album = self.root / "Artist" / "Album"
        self.album.mkdir(parents=True)
        self.audio = self.album / "01 Track.mp3"
        self.audio.write_text("audio", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_build_covit_command_includes_supported_query_and_remote_flags(self):
        import cover_fetch_highres as script

        command = script.build_covit_command(
            covit_path=Path("/tmp/covit"),
            audio_file=self.audio,
            query={"artist": "Artist", "album": "Album"},
        )

        self.assertIn("--query-artist", command)
        self.assertIn("Artist", command)
        self.assertIn("--query-album", command)
        self.assertIn("Album", command)
        self.assertIn("--browsers", command)
        self.assertIn("firefox", command)
        self.assertNotIn("--catch", command)
        self.assertIn("--remote-agent", command)
        self.assertIn("--remote-text", command)
        self.assertIn("https://covers.musichoarders.xyz", " ".join(command))
        self.assertIn("--query-country", command)
        self.assertIn("US", command)
        self.assertIn("--query-sources", command)
        self.assertIn(
            "tidal,bandcamp,itunes,amazonmusic,applemusic,lastfm,soulseek,soundcloud,discogs",
            command,
        )
        self.assertNotIn("--query-resolution", command)

    def test_process_album_folder_returns_opened_state_when_covit_launches(self):
        import cover_fetch_highres as script

        mocked_process = type("Proc", (), {"poll": lambda self: None})()
        with patch.object(script, "should_replace_cover", return_value=True), patch.object(
            script, "read_cover_query", return_value={"artist": "Artist", "album": "Album"}
        ), patch.object(script, "launch_covit", return_value=(mocked_process, 61207)) as mocked_launch, patch.object(
            script.Path, "exists", return_value=True
        ):
            result = script.process_album_folder(str(self.album), dry_run=False)

        self.assertEqual(result["status"], "opened")
        mocked_launch.assert_called_once()

    def test_process_album_folder_returns_error_when_covit_fails(self):
        import cover_fetch_highres as script

        with patch.object(script, "should_replace_cover", return_value=True), patch.object(
            script, "read_cover_query", return_value={"artist": "Artist", "album": "Album"}
        ), patch.object(script.subprocess, "Popen") as mocked_popen, patch.object(
            script.Path, "exists", return_value=True
        ), patch.object(script, "open_cover_search_in_browser", return_value=False):
            mocked_popen.return_value.poll.return_value = 2
            result = script.process_album_folder(str(self.album), dry_run=False)

        self.assertEqual(result["status"], "error")
        self.assertIn("exited with code 2", result["message"])

    def test_build_cover_search_url_uses_expected_defaults(self):
        import cover_fetch_highres as script

        url = script.build_cover_search_url({"artist": "Artist Name", "album": "Album Name"})
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "covers.musichoarders.xyz")
        self.assertEqual(params["artist"], ["Artist Name"])
        self.assertEqual(params["album"], ["Album Name"])
        self.assertEqual(params["country"], ["US"])
        self.assertEqual(
            params["sources"],
            ["tidal,bandcamp,itunes,amazonmusic,applemusic,lastfm,soulseek,soundcloud,discogs"],
        )

    def test_build_remote_cover_search_url_includes_remote_parameters(self):
        import cover_fetch_highres as script

        url = script.build_remote_cover_search_url({"artist": "Artist Name", "album": "Album Name"}, 52037)
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        self.assertEqual(params["remote.port"], ["52037"])
        self.assertEqual(params["artist"], ["Artist Name"])
        self.assertEqual(params["album"], ["Album Name"])

    def test_extract_listening_port_parses_stdout_line(self):
        import cover_fetch_highres as script

        self.assertEqual(script.extract_listening_port("Listening: 61207"), 61207)
        self.assertIsNone(script.extract_listening_port("Cover already high-res"))

    def test_process_album_folder_falls_back_to_browser_open_when_covit_fails(self):
        import cover_fetch_highres as script

        with patch.object(script, "should_replace_cover", return_value=True), patch.object(
            script, "read_cover_query", return_value={"artist": "Artist", "album": "Album"}
        ), patch.object(script.subprocess, "Popen") as mocked_popen, patch.object(
            script.Path, "exists", return_value=True
        ), patch.object(script, "open_cover_search_in_browser", return_value=True) as mocked_open:
            mocked_popen.return_value.poll.return_value = 1
            result = script.process_album_folder(str(self.album), dry_run=False)

        self.assertEqual(result["status"], "opened_fallback")
        mocked_open.assert_called_once_with({"artist": "Artist", "album": "Album"})

    def test_process_album_folder_opens_firefox_remote_url_when_default_browser_differs(self):
        import cover_fetch_highres as script

        mocked_process = type("Proc", (), {"poll": lambda self: None})()
        with patch.object(script, "should_replace_cover", return_value=True), patch.object(
            script, "read_cover_query", return_value={"artist": "Artist", "album": "Album"}
        ), patch.object(script, "launch_covit", return_value=(mocked_process, 61207)), patch.object(
            script.Path, "exists", return_value=True
        ), patch.object(
            script, "get_default_browser_bundle_id", return_value="com.brave.browser"
        ), patch.object(
            script, "open_url_in_browser_app", return_value=True
        ) as mocked_open:
            result = script.process_album_folder(str(self.album), dry_run=False)

        self.assertEqual(result["status"], "opened")
        mocked_open.assert_called_once()
        args = mocked_open.call_args.args
        self.assertEqual(args[1], "Firefox")
        self.assertIn("remote.port=61207", args[0])

    def test_maybe_prompt_continue_returns_false_when_user_stops(self):
        import cover_fetch_highres as script

        with patch.object(script.Confirm, "ask", return_value=False):
            should_continue = script.maybe_prompt_continue(wait_for_user=True)

        self.assertFalse(should_continue)


if __name__ == "__main__":
    unittest.main()
