# Music Archive Management Tools

Toolkit for maintaining a large music archive on macOS with interactive menu-driven workflows and direct Python scripts.

## Quick Start

Run the interactive menu:

```bash
python3 menu.py
```

Or double-click [launch.command](/Users/rd/.config/tools/hoarder-tools/launch.command) in Finder. It resolves the toolkit directory automatically, prefers Ghostty when available, and otherwise runs in the current terminal session.

The menu lets you:
- choose a tool by name
- answer option prompts interactively
- choose from numbered base-path presets
- append a relative subpath instead of typing full absolute paths
- run in `--dry-run` first
- rerun the same command for real immediately after a successful dry run

Current base-path presets include:
- `/Volumes/Eksternal/Audio`
- `/Volumes/Eksternal/Audio/Electronic`
- `/Volumes/Eksternal/Audio/Hip-Hop`
- `/Volumes/Eksternal/Audio/Metal`
- `/Volumes/Eksternal/Audio/Miscellaneous`
- `/Volumes/Eksternal/Audio/Punk & Hardcore`
- `/Volumes/Eksternal/Audio/Rock & Grunge`
- `/Volumes/Eksternal/Music/Nicotine+`
- `/Volumes/Eksternal/Music/Deemix`

Genre update tools default to the `Deemix` preset. Most library maintenance tools default to `/Volumes/Eksternal/Audio`.

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
│   ├── normalize_backdrops.py
│   ├── artist_image_normalize.py
│   ├── folder_remove_empty.py
│   ├── folder_remove_cover_only.py
│   ├── track_title_split_folder_fix.py
│   ├── archive_lossy_duplicates.py
│   ├── archive_mp3_duplicates.py
│   ├── track_validate_numbering.py
│   ├── metadata_generate_nfo.py
│   ├── metadata_update_genres_lastfm.py
│   ├── metadata_update_genres_discogs.py
│   ├── acquisition_discography_gaps.py
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
- `Normalize Backdrop File Names`
- `Download High-Resolution Cover Art`
- `Download Band Logos and Photos`

`Download High-Resolution Cover Art` opens Covers through COVIT as a manual workflow:
- defaults to `TIDAL`, `Bandcamp`, `iTunes`, `Amazon Music`, `Apple Music`, `Last.fm`, `Soulseek`, `SoundCloud`, and `Discogs`
- defaults to the `US` region
- does not set a minimum pixel query, so all sizes remain visible
- launches COVIT with a Firefox browser hint on macOS
- if your system default browser is something else, the tool also opens the live remote COVIT URL in Firefox so you can pick and save there
- waits for confirmation between albums by default so you can finish picking before the next search opens
- if COVIT exits unexpectedly, it falls back to opening the same Covers search in your browser for manual selection

Direct commands:

```bash
python3 scripts/cover_extract_embedded.py -d "/path/to/music" --dry-run
python3 scripts/cover_normalize_format.py -d "/path/to/music" --dry-run
python3 scripts/cover_normalize_case.py --archive "/path/to/music" --dry-run
python3 scripts/artist_image_normalize.py -d "/path/to/music" --dry-run
python3 scripts/normalize_backdrops.py -d "/path/to/music" --dry-run
python3 scripts/cover_fetch_highres.py -d "/path/to/music" --dry-run
python3 scripts/cover_fetch_highres.py -d "/path/to/music"
python3 scripts/cover_fetch_highres.py -d "/path/to/music" --no-wait
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
- `Update Genres From Last.fm`
- `Update Genres From Discogs`

Direct commands:

```bash
python3 scripts/track_validate_numbering.py --archive "/path/to/music" --strict
python3 scripts/metadata_generate_nfo.py -d "/path/to/music" --dry-run --verbose
python3 scripts/metadata_update_genres_lastfm.py -d "/path/to/music" --dry-run --verbose
python3 scripts/metadata_update_genres_discogs.py -d "/path/to/music" --dry-run --verbose
```

The genre update wrappers call your external Riley scripts on real runs and use a toolkit-native dry run to preview:
- affected MP3 files
- artists or artist/album pairs that would be queried
- files missing required tags

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

## Acquisition

- `Find Missing Discography Releases`
  - resolves an artist discography from Deezer using `band + known album`
  - compares those releases against your local collection using Riley's collection matcher
  - writes missing Deezer album URLs to a text file
  - can optionally prompt for specific missing releases to send to `deemon`
  - always scans first, then shows the missing list before any download choice is made

Direct command:

```bash
python3 scripts/acquisition_discography_gaps.py \
  -d "/Volumes/Eksternal/Audio" \
  --band "Radiohead" \
  --album "OK Computer" \
  --dry-run \
  --verbose \
  --output missing_discography_urls.txt
```

Real run with direct deemon handoff:

```bash
python3 scripts/acquisition_discography_gaps.py \
  -d "/Volumes/Eksternal/Audio" \
  --band "Radiohead" \
  --album "OK Computer" \
  --output missing_discography_urls.txt \
  --download-with-deemon
```

Notes:
- gap detection uses Riley's external collection matcher from `DeemixKit`
- direct downloading requires `deemon` to be installed and available in `PATH`
- the menu exposes this under the `Acquisition` category
- release selection accepts spaces, commas, or ranges such as `1 5 9` or `1-3,7`
- on download-enabled runs, pressing Enter at the selection prompt skips downloading instead of queueing everything

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
- The core toolkit is location-relative, so `menu.py` and `launch.command` can run from a moved copy of the repo.
- Some wrappers still depend on external fixed paths outside this repo:
  - `scripts/acquisition_discography_gaps.py`
  - `scripts/metadata_update_genres_lastfm.py`
  - `scripts/metadata_update_genres_discogs.py`
