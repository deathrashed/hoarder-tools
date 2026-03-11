# Music Archive Management Tools

Toolkit for maintaining a large music archive on macOS with interactive menu-driven workflows and direct Python scripts.

## Quick Start

Run the interactive menu:

```bash
python3 menu.py
```

The menu lets you:
- choose a tool by name
- answer option prompts interactively
- run in `--dry-run` first
- rerun the same command for real immediately after a successful dry run

## Project Layout

```text
hoarder-tools/
├── menu.py
├── scripts/
│   ├── lyrics_embed_from_lrc.py
│   ├── lyrics_find_missing_embedded.py
│   ├── cover_extract_embedded.py
│   ├── cover_normalize_format.py
│   ├── cover_normalize_case.py
│   ├── cover_fetch_highres.py
│   ├── artist_image_normalize.py
│   ├── folder_remove_empty.py
│   ├── folder_remove_cover_only.py
│   ├── track_title_split_folder_fix.py
│   ├── archive_lossy_duplicates.py
│   ├── archive_mp3_duplicates.py
│   ├── track_validate_numbering.py
│   ├── metadata_generate_nfo.py
│   └── metal_archives_scraper.py
├── archive/
│   ├── lyrics_remove_folders.py
│   ├── cover_remove_deprecated.py
│   ├── metadata_fetch_genres_lastfm.py
│   └── metadata_normalize_multi_artist.py
└── tests/
```

## Requirements

### Python

- Python 3.12+ is recommended
- `scripts/track_validate_numbering.py` uses `Path.walk()`, which requires Python 3.12

### Python Packages

```bash
pip install mutagen rich pillow requests beautifulsoup4 lxml
```

The exact packages you need depend on which scripts you use.

### Optional Tools

- `7zz` for archive workflows
- `COVIT` for high-resolution cover fetching
- `Lyrics Finder` for the missing-lyrics handoff workflow

## Primary Menu Workflows

### Lyrics

- `Embed Lyrics From LRC Files`
  - embeds matching `.lrc` files into FLAC and MP3 metadata
  - removes consumed `.lrc` files and empty `Lyrics` folders

- `Find Missing Embedded Lyrics`
  - scans for tracks without embedded lyrics
  - writes a newline-delimited path list
  - can prompt to open that saved list in Lyrics Finder after the scan

Direct commands:

```bash
python3 scripts/lyrics_embed_from_lrc.py -d "/path/to/music" --dry-run --verbose
python3 scripts/lyrics_embed_from_lrc.py -d "/path/to/music" --verbose

python3 scripts/lyrics_find_missing_embedded.py -d "/path/to/music" -o missing_embedded_lyrics.txt --verbose
python3 scripts/lyrics_find_missing_embedded.py -d "/path/to/music" -o missing_embedded_lyrics.txt --prompt-open-in-lyrics-finder
```

### Cover Art

- `Extract Embedded Cover Art`
- `Normalize Cover File Format`
- `Standardize Cover File Names`
- `Normalize Artist Folder Images`
- `Download High-Resolution Cover Art`
- `Download Band Logos and Photos`

Direct commands:

```bash
python3 scripts/cover_extract_embedded.py -d "/path/to/music" --dry-run
python3 scripts/cover_normalize_format.py -d "/path/to/music" --dry-run
python3 scripts/cover_normalize_case.py --archive "/path/to/music" --dry-run
python3 scripts/artist_image_normalize.py -d "/path/to/music" --dry-run
python3 scripts/cover_fetch_highres.py -d "/path/to/music" --dry-run
python3 scripts/metal_archives_scraper.py --path "/path/to/music" --all
```

### Cleanup

- `Remove Folders Without Audio Files`
- `Remove Empty and Cover-Only Folders`
- `Fix Split Track Title Folders`

The split-track fixer repairs bad folder structures created when `/` in a title was treated as a path separator. Repaired filenames use the fullwidth slash `／`, not `_`.

Direct commands:

```bash
python3 scripts/folder_remove_empty.py -d "/path/to/music" --dry-run --verbose
python3 scripts/folder_remove_cover_only.py -d "/path/to/music" --dry-run --verbose
python3 scripts/track_title_split_folder_fix.py -d "/path/to/music" --dry-run --verbose
```

If you run the split-track fixer directly, it can prompt to apply the same changes immediately after the dry run:

```bash
python3 scripts/track_title_split_folder_fix.py -d "/path/to/music" --dry-run --prompt-apply-after-dry-run
```

### Archive

- `Archive Lossy Duplicates`
- `Archive MP3 Duplicates`

Direct commands:

```bash
python3 scripts/archive_lossy_duplicates.py -d "/path/to/music" --dry-run --format tar.xz
python3 scripts/archive_mp3_duplicates.py -d "/path/to/music" --dry-run --format tar.xz
```

### Metadata and Validation

- `Check Track Numbering`
- `Generate Album and Artist Info Files`

Direct commands:

```bash
python3 scripts/track_validate_numbering.py --archive "/path/to/music" --strict
python3 scripts/metadata_generate_nfo.py -d "/path/to/music" --dry-run --verbose
```

## Lyrics Finder Workflow

The current supported Lyrics Finder flow is:

1. scan for tracks missing embedded lyrics
2. save the results to a path list
3. optionally send that saved list to Lyrics Finder

Example:

```bash
python3 scripts/lyrics_find_missing_embedded.py \
  -d "/path/to/music" \
  -o missing_embedded_lyrics.txt \
  --prompt-open-in-lyrics-finder
```

There is still a direct helper script if you want to open an existing saved list manually:

```bash
python3 scripts/lyrics_send_to_lyrics_finder.py --path-list missing_embedded_lyrics.txt
```

That helper is intentionally no longer a primary menu item.

## Legacy / One-Off Scripts

These stay outside the main menu and are meant to be run directly when needed:

- `archive/lyrics_remove_folders.py`
- `archive/cover_remove_deprecated.py`
- `archive/metadata_fetch_genres_lastfm.py`
- `archive/metadata_normalize_multi_artist.py`

## Notes

- `lyrics_fetch_metal_archives.py` was removed because it is not a reliable workflow here.
- The menu is the recommended entrypoint for normal use.
- For destructive tools, use `--dry-run` first.
- The menu can now offer an immediate real rerun after a successful dry run, so you do not need to go back through the menu.
