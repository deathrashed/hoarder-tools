import unittest
from pathlib import Path
from unittest.mock import patch


class FakeMatcher:
    def __init__(self, existing):
        self.existing = existing

    def is_album_in_collection(self, artist, album, year):
        return (artist, album) in self.existing


class AcquisitionDiscographyGapTests(unittest.TestCase):
    def test_resolve_matcher_collection_path_uses_audio_library_root(self):
        import acquisition_discography_gaps as script

        path = Path("/Volumes/Eksternal/Audio/Hip-Hop/N/Nas")

        self.assertEqual(
            script.resolve_matcher_collection_path(path),
            Path("/Volumes/Eksternal/Audio"),
        )

    def test_filter_discography_excludes_singles_by_default(self):
        import acquisition_discography_gaps as script

        albums = [
            {"id": 1, "title": "Album A", "record_type": "album"},
            {"id": 2, "title": "EP A", "record_type": "ep"},
            {"id": 3, "title": "Single A", "record_type": "single"},
        ]

        filtered = script.filter_discography(albums, include_singles=False)

        self.assertEqual([album["title"] for album in filtered], ["Album A", "EP A"])

    def test_parse_release_selection_supports_space_numbers(self):
        import acquisition_discography_gaps as script

        selected = script.parse_release_selection("1 5 9 11 8 4", total=14)

        self.assertEqual(selected, [1, 4, 5, 8, 9, 11])

    def test_select_releases_by_numbers_returns_requested_items(self):
        import acquisition_discography_gaps as script

        releases = [
            {"album": "Album 1"},
            {"album": "Album 2"},
            {"album": "Album 3"},
            {"album": "Album 4"},
        ]

        selected = script.select_releases_by_numbers(releases, [4, 2])

        self.assertEqual([release["album"] for release in selected], ["Album 2", "Album 4"])

    def test_prompt_for_release_subset_returns_empty_when_skipping(self):
        import acquisition_discography_gaps as script

        releases = [{"album": "Album 1"}, {"album": "Album 2"}]

        with patch.object(script.Prompt, "ask", return_value=""):
            selected = script.prompt_for_release_subset(releases)

        self.assertEqual(selected, [])

    def test_split_missing_releases_separates_existing_collection_matches(self):
        import acquisition_discography_gaps as script

        releases = [
            {"artist": "Artist", "album": "Album A", "year": "2001", "deezer_url": "https://www.deezer.com/album/1"},
            {"artist": "Artist", "album": "Album B", "year": "2002", "deezer_url": "https://www.deezer.com/album/2"},
        ]

        missing, existing = script.split_missing_releases(releases, FakeMatcher({("Artist", "Album A")}))

        self.assertEqual([release["album"] for release in missing], ["Album B"])
        self.assertEqual([release["album"] for release in existing], ["Album A"])

    def test_download_with_deemon_builds_url_arguments(self):
        import acquisition_discography_gaps as script

        releases = [
            {"deezer_url": "https://www.deezer.com/album/1"},
            {"deezer_url": "https://www.deezer.com/album/2"},
        ]

        with patch.object(script, "resolve_deemon_command", return_value=["deemon"]), patch.object(
            script.subprocess, "run"
        ) as mocked_run:
            mocked_run.return_value.returncode = 0
            result = script.download_with_deemon(releases)

        self.assertEqual(result, 0)
        mocked_run.assert_called_once_with(
            [
                "deemon",
                "download",
                "--url",
                "https://www.deezer.com/album/1",
                "--url",
                "https://www.deezer.com/album/2",
            ],
            check=False,
        )


if __name__ == "__main__":
    unittest.main()
