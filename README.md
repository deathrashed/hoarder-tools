# Music Archive Management Scripts

<div align="center">

[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](https://opensource.org/licenses/MIT) [![Python](https://img.shields.io/badge/Python-3.6%2B-green?style=for-the-badge&logo=python)](https://www.python.org/) [![Scripts](https://img.shields.io/badge/Scripts-14+-orange?style=for-the-badge)](https://github.com/deathrashed/hoarder-tools) [![macOS](https://img.shields.io/badge/macOS-Compatible-black?style=for-the-badge&logo=apple)](https://www.apple.com/macos/)

**A comprehensive collection of Python scripts for managing a lossless music archive with professional-grade organization and automation.**

</div>

## 🎯 Purpose

This suite is designed for music hoarders who maintain large lossless collections with:

- **FLAC files** as primary format
- **Lossy duplicates** archived for space efficiency
- **Standardized cover art** and metadata
- **Embedded lyrics** and documentation

Whether you're:

- Organizing a massive music collection
- Converting from lossy to lossless formats
- Managing cover art and metadata
- Archiving duplicate files
- Maintaining collection quality standards

These scripts provide professional-grade automation with safety features and comprehensive format support.

## 📊 Script Overview

<table>
  <tr>
    <th>Script</th>
    <th>Category</th>
    <th>Complexity</th>
    <th>Key Feature</th>
    <th>Safety Level</th>
  </tr>
  <tr>
    <td><a href="#cover-extract">cover_extract.py</a></td>
    <td>🖼️ Cover Art</td>
    <td>Low</td>
    <td>Extract embedded covers</td>
    <td>🟢 Safe</td>
  </tr>
  <tr>
    <td><a href="#cover-normalize">cover_normalize.py</a></td>
    <td>🖼️ Cover Art</td>
    <td>Low</td>
    <td>Standardize formats</td>
    <td>🟢 Safe</td>
  </tr>
  <tr>
    <td><a href="#case-normalize">case_normalize.py</a></td>
    <td>🖼️ Cover Art</td>
    <td>Low</td>
    <td>Lowercase naming</td>
    <td>🟢 Safe</td>
  </tr>
  <tr>
    <td><a href="#covit-fetch">covit_fetch.py</a></td>
    <td>🖼️ Cover Art</td>
    <td>Medium</td>
    <td>High-res cover fetching</td>
    <td>🟡 External tool</td>
  </tr>
  <tr>
    <td><a href="#cover-purge">cover_purge.py</a></td>
    <td>🖼️ Cover Art</td>
    <td>Low</td>
    <td>Remove deprecated formats</td>
    <td>🟡 Destructive</td>
  </tr>
  <tr>
    <td><a href="#folder-prune">folder_prune.py</a></td>
    <td>📁 Organization</td>
    <td>Low</td>
    <td>Remove empty folders</td>
    <td>🟡 Destructive</td>
  </tr>
  <tr>
    <td><a href="#mp3-archive">mp3_archive.py</a></td>
    <td>📁 Organization</td>
    <td>Medium</td>
    <td>Archive MP3 duplicates</td>
    <td>🟡 Destructive</td>
  </tr>
  <tr>
    <td><a href="#lossy-archive">lossy_archive.py</a></td>
    <td>📁 Organization</td>
    <td>Medium</td>
    <td>Archive lossy duplicates</td>
    <td>🟡 Destructive</td>
  </tr>
  <tr>
    <td><a href="#lyrics-embed">lyrics_embed.py</a></td>
    <td>🎵 Lyrics</td>
    <td>Medium</td>
    <td>Embed lyrics from LRC files</td>
    <td>🟡 Destructive</td>
  </tr>
  <tr>
    <td><a href="#lyrics-purge">lyrics_purge.py</a></td>
    <td>🎵 Lyrics</td>
    <td>Low</td>
    <td>Remove lyrics folders</td>
    <td>🟡 Destructive</td>
  </tr>
  <tr>
    <td><a href="#nfo-generate">nfo_generate.py</a></td>
    <td>📝 Metadata</td>
    <td>Low</td>
    <td>Generate documentation</td>
    <td>🟢 Safe</td>
  </tr>
  <tr>
    <td><a href="#track-gap-checker">track_gap_checker.py</a></td>
    <td>🔍 Quality Control</td>
    <td>Low</td>
    <td>Validate track numbering</td>
    <td>🟢 Safe</td>
  </tr>
</table>

## 🛠️ Requirements

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
  - Install from: https://covers.musichoarders.xyz/
  - Place at: `~/.config/tools/covit`

### Python Version

- Python 3.6+ required
- Python 3.8+ recommended

## 📂 Script Categories

<table>
  <tr>
    <td width="50%" valign="top">
      <h3>🖼️ Cover Art Management</h3>
      <ul>
        <li><b><a href="#cover-extract">cover_extract.py</a></b> - Extract embedded cover art from audio files and save as standardized images.</li>
        <li><b><a href="#cover-normalize">cover_normalize.py</a></b> - Convert PNG to JPG and standardize cover art naming conventions.</li>
        <li><b><a href="#case-normalize">case_normalize.py</a></b> - Enforce lowercase naming for all cover art files and folders.</li>
        <li><b><a href="#covit-fetch">covit_fetch.py</a></b> - Fetch high-resolution cover art using external COVIT tool.</li>
        <li><b><a href="#cover-purge">cover_purge.py</a></b> - Remove deprecated image formats (.jp2, .jxl) from your collection.</li>
      </ul>
      <h3>📁 File Organization & Cleanup</h3>
      <ul>
        <li><b><a href="#folder-prune">folder_prune.py</a></b> - Remove empty folders that contain no audio files.</li>
        <li><b><a href="#mp3-archive">mp3_archive.py</a></b> - Archive MP3 duplicates of FLAC files with comprehensive format support.</li>
        <li><b><a href="#lossy-archive">lossy_archive.py</a></b> - Archive various lossy format duplicates with customizable options.</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h3>🎵 Lyrics Management</h3>
      <ul>
        <li><b><a href="#lyrics-embed">lyrics_embed.py</a></b> - Embed lyrics from .lrc files into audio metadata and clean up.</li>
        <li><b><a href="#lyrics-purge">lyrics_purge.py</a></b> - Remove all leftover Lyrics folders after embedding.</li>
      </ul>
      <h3>📝 Metadata & Documentation</h3>
      <ul>
        <li><b><a href="#nfo-generate">nfo_generate.py</a></b> - Generate album.nfo and artist.nfo documentation files.</li>
      </ul>
      <h3>🔍 Quality Control</h3>
      <ul>
        <li><b><a href="#track-gap-checker">track_gap_checker.py</a></b> - Validate track numbering and detect gaps in album sequences.</li>
      </ul>
    </td>
  </tr>
</table>

## 🎭 Real-World Use Cases

<details>
<summary><b>Collection Migration</b></summary>
<ul>
  <li><b>FLAC Conversion</b> - Use <a href="#lossy-archive">lossy_archive.py</a> to archive old MP3s after upgrading to FLAC</li>
  <li><b>Cover Art Standardization</b> - Run <a href="#cover-extract">cover_extract.py</a> → <a href="#cover-normalize">cover_normalize.py</a> → <a href="#case-normalize">case_normalize.py</a></li>
  <li><b>Quality Validation</b> - Use <a href="#track-gap-checker">track_gap_checker.py</a> to ensure proper track numbering</li>
  <li><b>Documentation</b> - Generate <a href="#nfo-generate">nfo files</a> for comprehensive collection metadata</li>
</ul>
</details>

<details>
<summary><b>Ongoing Maintenance</b></summary>
<ul>
  <li><b>Monthly Cleanup</b> - Run <a href="#folder-prune">folder_prune.py</a> to remove empty directories</li>
  <li><b>Lyrics Integration</b> - Use <a href="#lyrics-embed">lyrics_embed.py</a> for new albums with LRC files</li>
  <li><b>Duplicate Management</b> - Archive new MP3s with <a href="#mp3-archive">mp3_archive.py</a></li>
  <li><b>Format Updates</b> - Use <a href="#cover-purge">cover_purge.py</a> to remove deprecated image formats</li>
</ul>
</details>

<details>
<summary><b>Professional Workflows</b></summary>
<ul>
  <li><b>Music Librarian</b> - Complete workflow from ingestion to archival with quality control</li>
  <li><b>DJ Collection</b> - Maintain organized, documented collection with embedded metadata</li>
  <li><b>Archive Curator</b> - Long-term preservation with comprehensive documentation</li>
  <li><b>Lossless Enthusiast</b> - Transition from lossy to lossless with proper duplicate management</li>
</ul>
</details>

## 🖼️ Cover Art Management

### <a name="cover-extract"></a>`cover_extract.py`

**Purpose:** Extracts embedded cover art from audio files

- Reads cover art from FLAC and MP3 metadata
- Saves as `cover.jpg` in each album folder
- Skips files that already have cover art

**Usage:**

```bash
python cover_extract.py -d /path/to/music --dry-run
python cover_extract.py -d /path/to/music
```

### <a name="cover-normalize"></a>`cover_normalize.py`

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

### <a name="case-normalize"></a>`case_normalize.py`

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

### <a name="covit-fetch"></a>`covit_fetch.py`

**Purpose:** Fetches high-resolution cover art using COVIT

- Checks for existing covers under 1000x1000 pixels
- Uses COVIT to fetch from multiple sources (Apple Music, Amazon, Bandcamp, Deezer)
- Requires COVIT installation

**Usage:**

```bash
python covit_fetch.py -d /path/to/music --dry-run
python covit_fetch.py --archive /path/to/music
```

### <a name="cover-purge"></a>`cover_purge.py`

**Purpose:** Removes deprecated image formats

- Deletes `.jp2` and `.jxl` files
- Cleans up old/unsupported image formats

**Usage:**

```bash
python cover_purge.py -d /path/to/music --dry-run
python cover_purge.py -d /path/to/music --verbose
```

## 📁 File Organization & Cleanup

### <a name="folder-prune"></a>`folder_prune.py`

**Purpose:** Removes empty folders without audio files

- Recursively scans for folders containing no audio
- Preserves folders with any audio files (FLAC, MP3, etc.)
- Safe deletion with dry-run mode

**Usage:**

```bash
python folder_prune.py -d /path/to/music --dry-run
python folder_prune.py -d /path/to/music --verbose
```

### <a name="mp3-archive"></a>`mp3_archive.py`

**Purpose:** Archives MP3 duplicates of FLAC files

- Finds MP3s that have matching FLAC files
- Creates archives containing the MP3s in various formats
- Optionally deletes original MP3s after archiving
- Skips files already in existing archives
- Supports comprehensive archive formats: 7z, zip, tar.gz, tar.xz, tar.bz2, xz, gzip, bzip2

**Usage:**

```bash
python mp3_archive.py -d /path/to/music --dry-run
python mp3_archive.py -d /path/to/music --format zip --keep  # Keep originals
python mp3_archive.py -d /path/to/music --format tar.gz --verbose
python mp3_archive.py -d /path/to/music --format tar.xz  # High compression
python mp3_archive.py -d /path/to/music --format gzip  # Fast compression
python mp3_archive.py -d /path/to/music --format bzip2  # Maximum compression
```

### <a name="lossy-archive"></a>`lossy_archive.py`

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

## 🎵 Lyrics Management

### <a name="lyrics-embed"></a>`lyrics_embed.py`

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

### <a name="lyrics-purge"></a>`lyrics_purge.py`

**Purpose:** Removes all `Lyrics` folders

- Cleanup script to remove leftover lyrics folders
- Useful after running `lyrics_embed.py`

**Usage:**

```bash
python lyrics_purge.py -d /path/to/music --dry-run
python lyrics_purge.py -d /path/to/music --verbose
```

## 📝 Metadata & Documentation

### <a name="nfo-generate"></a>`nfo_generate.py`

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

## 🔍 Quality Control

### <a name="track-gap-checker"></a>`track_gap_checker.py`

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

## 🚀 Common Workflows

<details>
<summary><b>Initial Setup Workflow</b></summary>
<p>Perfect for setting up a new collection or migrating from lossy to lossless:</p>

```bash
# 1. Extract embedded covers
python cover_extract.py -d /path/to/music --dry-run
python cover_extract.py -d /path/to/music

# 2. Normalize cover formats
python cover_normalize.py -d /path/to/music --dry-run
python cover_normalize.py -d /path/to/music

# 3. Fetch missing high-res covers (optional)
python covit_fetch.py -d /path/to/music --dry-run
python covit_fetch.py -d /path/to/music

# 4. Standardize naming
python case_normalize.py --archive /path/to/music --dry-run
python case_normalize.py --archive /path/to/music

# 5. Validate collection
python track_gap_checker.py --archive /path/to/music
```

</details>

<details>
<summary><b>Regular Maintenance Workflow</b></summary>
<p>Monthly maintenance routine for ongoing collection management:</p>

```bash
# 1. Check track numbering
python track_gap_checker.py --archive /path/to/music

# 2. Archive new duplicates
python lossy_archive.py -d /path/to/music --dry-run
python lossy_archive.py -d /path/to/music --format tar.xz

# 3. Embed lyrics for new albums
python lyrics_embed.py -d /path/to/music --dry-run
python lyrics_embed.py -d /path/to/music --verbose

# 4. Clean up empty folders
python folder_prune.py -d /path/to/music --dry-run
python folder_prune.py -d /path/to/music --verbose

# 5. Remove lyrics folders
python lyrics_purge.py -d /path/to/music --dry-run
python lyrics_purge.py -d /path/to/music --verbose

# 6. Generate updated documentation
python nfo_generate.py -d /path/to/music --dry-run
python nfo_generate.py -d /path/to/music --verbose
```

</details>

<details>
<summary><b>Deep Cleanup Workflow</b></summary>
<p>Comprehensive cleanup for collections with legacy issues:</p>

```bash
# 1. Remove deprecated formats
python cover_purge.py -d /path/to/music --dry-run
python cover_purge.py -d /path/to/music --verbose

# 2. Archive all lossy duplicates
python mp3_archive.py -d /path/to/music --dry-run
python mp3_archive.py -d /path/to/music --format 7z

# 3. Archive other lossy formats
python lossy_archive.py -d /path/to/music --dry-run
python lossy_archive.py -d /path/to/music --ext aac ogg m4a --format zip

# 4. Remove empty directories
python folder_prune.py -d /path/to/music --dry-run
python folder_prune.py -d /path/to/music --verbose

# 5. Final validation
python track_gap_checker.py --archive /path/to/music --strict
```

</details>

## 🛡️ Safety Features

- **🟢 Dry-run mode:** All scripts support `--dry-run` to preview changes
- **📝 Verbose output:** Detailed logging with `--verbose` flag
- **⚠️ Error handling:** Graceful handling of missing files/tools
- **🎨 Rich console:** Colored output for clear status reporting
- **🔒 Safe defaults:** Non-destructive operations by default

## 💡 Pro Tips

- Always run with `--dry-run` first to preview changes
- Use `--verbose` for detailed output during processing
- Process in small batches for large collections
- Keep backups before running archiving scripts
- COVIT integration is optional but recommended for cover fetching
- Use `tar.xz` format for maximum compression in archiving
- Use `gzip` format for fastest compression when speed matters

## 🔧 Troubleshooting

<details>
<summary><b>Common Issues</b></summary>
<ul>
  <li><b>7-Zip errors:</b> Ensure <code>7zz</code> command is available in PATH</li>
  <li><b>COVIT not found:</b> Check installation path in <code>covit_fetch.py</code></li>
  <li><b>Permission errors:</b> Run with appropriate file permissions</li>
  <li><b>Memory issues:</b> Process smaller directory trees for large collections</li>
</ul>
</details>

<details>
<summary><b>Performance Optimization</b></summary>
<ul>
  <li><b>Large collections:</b> Process by artist or year subdirectories</li>
  <li><b>Network drives:</b> Copy to local drive for processing, then move back</li>
  <li><b>SSD storage:</b> Use SSD for temporary archiving operations</li>
  <li><b>Parallel processing:</b> Run multiple scripts on different directory trees</li>
</ul>
</details>

## 🤝 Contributing

Contributions are welcome! Feel free to:

- Submit additional script ideas
- Suggest improvements to existing scripts
- Share your experiences and customizations
- Report issues or suggest clarifications

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

<div align="center">
  <p>Created for the music hoarding community</p>
  <p>
    <a href="https://github.com/deathrashed/hoarder-tools"><img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"></a>
  </p>
</div>
