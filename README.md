# Music Archive Management Scripts

A comprehensive collection of Python scripts for managing a lossless music archive. These tools help organize, clean, and maintain a music collection with FLAC as the primary format.

## Overview

This suite is designed for music hoarders who maintain large lossless collections with:
- FLAC files as primary format
- Lossy duplicates archived for space efficiency
- Standardized cover art and metadata
- Embedded lyrics and documentation

## Requirements

### Python Dependencies
```bash
pip install mutagen rich pillow
```

### System Tools
- **7-Zip** (`7zz` command) - For archiving duplicate files
  ```bash
  brew install 7zip  # macOS
  ```
- **COVIT** (optional) - For high-res cover fetching
  - Install from: https://github.com/porphyry/covit
  - Place at: `/Users/rd/.config/tools/covit`

### Python Version
- Python 3.6+ required
- Python 3.8+ recommended

## Scripts Overview

### 🖼️ Cover Art Management

#### `case_normalize.py`
**Purpose:** Standardizes cover art filenames to lowercase
- Renames `Cover.JPG` → `cover.jpg`
- Renames `Folder.JPEG` → `cover.jpg`
- Renames `Album Cover.jpg` → `cover.jpg`
- Handles artist-level `folder.jpg` → `artist.jpg`

**Usage:**
```bash
python case_normalize.py --archive /path/to/music --dry-run
python case_normalize.py --archive /path/to/music
```

#### `cover_extract.py`
**Purpose:** Extracts embedded cover art from audio files
- Reads cover art from FLAC and MP3 metadata
- Saves as `cover.jpg` in each album folder
- Skips files that already have cover art

**Usage:**
```bash
python cover_extract.py -d /path/to/music --dry-run
python cover_extract.py -d /path/to/music
```

#### `cover_normalize.py`
**Purpose:** Normalizes cover art formats and naming
- Converts PNG files to JPG (quality 90)
- Renames various cover patterns to `cover.jpg`
- Removes CD art files (`cdart.*`)
- Preserves `logo.png` files

**Usage:**
```bash
python cover_normalize.py -d /path/to/music --dry-run
python cover_normalize.py -d /path/to/music
```

#### `cover_purge.py`
**Purpose:** Removes deprecated image formats
- Deletes `.jp2` and `.jxl` files
- Cleans up old/unsupported image formats

**Usage:**
```bash
python cover_purge.py -d /path/to/music --dry-run
python cover_purge.py -d /path/to/music --verbose
```

#### `covit_fetch.py`
**Purpose:** Fetches high-resolution cover art using COVIT
- Checks for existing covers under 1000x1000 pixels
- Uses COVIT to fetch from multiple sources (Apple Music, Amazon, Bandcamp, Deezer)
- Requires COVIT installation

**Usage:**
```bash
python covit_fetch.py -d /path/to/music --dry-run
python covit_fetch.py --archive /path/to/music
```

### 📁 File Organization & Cleanup

#### `folder_prune.py`
**Purpose:** Removes empty folders without audio files
- Recursively scans for folders containing no audio
- Preserves folders with any audio files (FLAC, MP3, etc.)
- Safe deletion with dry-run mode

**Usage:**
```bash
python folder_prune.py -d /path/to/music --dry-run
python folder_prune.py -d /path/to/music --verbose
```

#### `mp3_archive.py`
**Purpose:** Archives MP3 duplicates of FLAC files
- Finds MP3s that have matching FLAC files
- Creates archives containing the MP3s in various formats
- Optionally deletes original MP3s after archiving
- Skips files already in existing archives
- Supports multiple archive formats: 7z, zip, tar.gz, tar.xz, tar.bz2, xz, gzip, bzip2

**Usage:**
```bash
python mp3_archive.py -d /path/to/music --dry-run
python mp3_archive.py -d /path/to/music --format zip --keep  # Keep originals
python mp3_archive.py -d /path/to/music --format tar.gz --verbose
python mp3_archive.py -d /path/to/music --format xz  # High compression
```

#### `lossy_archive.py`
**Purpose:** Archives various lossy format duplicates
- Handles MP3, AAC, OGG, M4A, WAV duplicates
- Creates archives in various formats (7z, zip, tar.gz, etc.)
- More comprehensive than `mp3_archive.py`
- Customizable format selection and file extensions

**Usage:**
```bash
python lossy_archive.py -d /path/to/music --dry-run
python lossy_archive.py -d /path/to/music --ext mp3 aac ogg --format zip --keep
python lossy_archive.py -d /path/to/music --format tar.xz --verbose
python lossy_archive.py -d /path/to/music --format bzip2  # High compression
```

### 🎵 Lyrics Management

#### `lyrics_embed.py`
**Purpose:** Embeds lyrics from .lrc files into audio files
- Finds matching `.lrc` files for each audio file
- Strips timestamps from lyrics
- Embeds into FLAC and MP3 metadata
- Deletes `.lrc` files and empty `Lyrics` folders after embedding

**Usage:**
```bash
python lyrics_embed.py -d /path/to/music --dry-run
python lyrics_embed.py -d /path/to/music --verbose
```

#### `lyrics_purge.py`
**Purpose:** Removes all `Lyrics` folders
- Cleanup script to remove leftover lyrics folders
- Useful after running `lyrics_embed.py`

**Usage:**
```bash
python lyrics_purge.py -d /path/to/music --dry-run
python lyrics_purge.py -d /path/to/music --verbose
```

### 📝 Metadata & Documentation

#### `nfo_generate.py`
**Purpose:** Creates metadata documentation files
- Generates `album.nfo` and `artist.nfo` files
- Extracts metadata from audio files (artist, album, year, genre)
- Documents cover art and lyrics status
- Provides structured documentation for each album/artist

**Usage:**
```bash
python nfo_generate.py -d /path/to/music --dry-run
python nfo_generate.py -d /path/to/music --verbose
```

### 🔍 Quality Control

#### `track_gap_checker.py`
**Purpose:** Validates track numbering in album folders
- Detects missing track numbers (gaps in sequence)
- Identifies inconsistent numbering
- Strict mode flags albums not starting at track 01
- Warns about large jumps in track numbers

**Usage:**
```bash
python track_gap_checker.py --archive /path/to/music
python track_gap_checker.py --archive /path/to/music --strict
```

## Common Workflow

### Initial Setup
1. **Extract embedded covers:** `cover_extract.py`
2. **Normalize cover formats:** `cover_normalize.py`
3. **Fetch missing covers:** `covit_fetch.py`
4. **Standardize naming:** `case_normalize.py`

### Regular Maintenance
1. **Check track numbering:** `track_gap_checker.py`
2. **Archive duplicates:** `lossy_archive.py`
3. **Embed lyrics:** `lyrics_embed.py`
4. **Clean up:** `folder_prune.py`, `lyrics_purge.py`
5. **Generate docs:** `nfo_generate.py`

### Cleanup Tasks
1. **Remove deprecated formats:** `cover_purge.py`
2. **Remove empty folders:** `folder_prune.py`
3. **Remove lyrics folders:** `lyrics_purge.py`

## Safety Features

- **Dry-run mode:** All scripts support `--dry-run` to preview changes
- **Verbose output:** Detailed logging with `--verbose` flag
- **Error handling:** Graceful handling of missing files/tools
- **Rich console:** Colored output for clear status reporting

## Tips

- Always run with `--dry-run` first to preview changes
- Use `--verbose` for detailed output during processing
- Process in small batches for large collections
- Keep backups before running archiving scripts
- COVIT integration is optional but recommended for cover fetching

## Troubleshooting

- **7-Zip errors:** Ensure `7zz` command is available in PATH
- **COVIT not found:** Check installation path in `covit_fetch.py`
- **Permission errors:** Run with appropriate file permissions
- **Memory issues:** Process smaller directory trees for large collections
