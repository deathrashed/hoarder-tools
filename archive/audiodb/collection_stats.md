# Collection Statistics Generator

Comprehensive analysis tool for your music collection. Generates detailed statistics about artists, albums, tracks, formats, artwork coverage, and documentation completeness.

## Quick Start

```bash
# Default path (/Volumes/Eksternal/Audio)
python3 collection_stats.py

# Custom path
python3 collection_stats.py /path/to/your/Audio
```

## Features

- **Complete collection analysis** - Artists, albums, tracks by genre
- **Storage statistics** - Total size and by genre
- **Format distribution** - MP3, FLAC, etc. with percentages
- **Decade analysis** - Albums by decade (1960s-2020s)
- **Artwork coverage** - Albums with covers, artists with logos
- **Documentation tracking** - info.txt, album_info.md, artist docs
- **Special collections** - Compilations, splits, singles

## Usage

### Basic Usage

```bash
# Analyze collection at default path
python3 collection_stats.py

# Analyze collection at custom path
python3 collection_stats.py /Volumes/OtherDrive/Music
```

### Output Files

The script generates two files in the same directory as your Audio folder:

1. **`stats.json`** - Machine-readable JSON with complete statistics
2. **`STATS.md`** - Human-readable markdown report

Example location:
```
/Volumes/Eksternal/Audio/
├── stats.json
└── STATS.md
```

## What It Analyzes

### Collection Structure

- **Artists** - Total count and by genre
- **Albums** - Total count and by genre
- **Tracks** - Total count and by genre
- **Storage** - Total size in GB and by genre

### Audio Formats

Tracks analyzed by format:
- MP3
- FLAC
- M4A
- WAV
- OGG
- WMA
- AAC
- Opus

Shows count and percentage for each format.

### Albums by Decade

Distribution of albums across decades:
- 1960s
- 1970s
- 1980s
- 1990s
- 2000s
- 2010s
- 2020s

### Artwork Coverage

- **Album covers** - Albums with `cover.jpg` or `cover.png`
- **Artist logos** - Artists with logo files (logo.png, logo.jpg, etc.)

Shows counts and percentages.

### Documentation Coverage

- **info.txt files** - Albums with info.txt
- **album_info.md files** - Albums with album_info.md
- **Artist documentation** - Artists with .md or .pdf files

### Special Collections

- **Compilations** - Albums in `-Compilations-` folders
- **Splits** - Albums in `-Splits-` folders
- **Singles** - Albums in `-Singles-` folders

## Example Output

### Terminal Output

```
=== Collection Statistics Generator ===

Scanning Metal...
Scanning Punk & Hardcore...
Scanning Electronic...
Scanning Hip-Hop...
Scanning Rock & Grunge...
Scanning Miscellaneous...

✓ JSON saved to: /Volumes/Eksternal/Audio/stats.json
✓ Markdown saved to: /Volumes/Eksternal/Audio/STATS.md

✨ Statistics generation complete!
```

### Markdown Report (STATS.md)

```markdown
# Collection Statistics

*Generated: January 7, 2026 at 3:45 PM*

## Overview

12,345 tracks across 1,234 albums from 567 artists, organized into 6 major genres.

**Total Storage**: 234.56 GB

## By Genre

| Genre | Artists | Albums | Tracks | Storage |
|-------|---------|--------|--------|---------|
| Metal | 234 | 567 | 4,567 | 89.12 GB |
| Punk & Hardcore | 123 | 234 | 2,345 | 45.67 GB |
...

## Audio Formats

- **.flac**: 6,789 tracks (55.0%)
- **.mp3**: 4,567 tracks (37.0%)
- **.m4a**: 989 tracks (8.0%)

## Albums by Decade

- **1990s**: 234 albums
- **2000s**: 456 albums
- **2010s**: 345 albums
...

## Artwork Coverage

- **Album Covers**: 1,123 / 1,234 albums (91.0%)
- **Artist Logos**: 456 / 567 artists (80.4%)

## Documentation

- **info.txt files**: 890 albums (72.1%)
- **album_info.md files**: 234 albums (19.0%)
- **Artist documentation**: 123 artists
```

### JSON Output (stats.json)

```json
{
  "generated_at": "2026-01-07T15:45:00",
  "genres": {
    "Metal": {
      "artists": 234,
      "albums": 567,
      "tracks": 4567,
      "size_gb": 89.12
    },
    ...
  },
  "totals": {
    "artists": 567,
    "albums": 1234,
    "tracks": 12345,
    "size_gb": 234.56
  },
  "formats": {
    ".flac": 6789,
    ".mp3": 4567,
    ...
  },
  "decades": {
    "1990": 234,
    "2000": 456,
    ...
  },
  "artwork_coverage": {
    "albums_with_covers": 1123,
    "albums_without_covers": 111,
    "artists_with_logos": 456,
    "artists_without_logos": 111
  },
  ...
}
```

## Integration

### Using JSON Output in Scripts

```python
#!/usr/bin/env python3
import json

with open('/Volumes/Eksternal/Audio/stats.json') as f:
    stats = json.load(f)

print(f"Total artists: {stats['totals']['artists']}")
print(f"Total albums: {stats['totals']['albums']}")
print(f"Total storage: {stats['totals']['size_gb']} GB")

# By genre
for genre, data in stats['genres'].items():
    print(f"{genre}: {data['albums']} albums")
```

### Finding Gaps

```bash
# Find bands missing logos
python3 collection_stats.py
# Check STATS.md for artwork coverage

# Then use band_image_scraper.py to fill gaps
./band_image_scraper.py --letter D
```

## Performance

Scanning speed depends on collection size:
- **Small collection (500 albums):** ~30 seconds
- **Medium collection (2,000 albums):** ~2 minutes
- **Large collection (5,000+ albums):** ~5-10 minutes

The script must traverse every directory and file to gather accurate statistics.

## Collection Structure Assumptions

The script expects this structure:

```
Audio/
├── Metal/
│   ├── A/
│   │   ├── Artist1/
│   │   │   ├── 1990 - Album1/
│   │   │   └── 1992 - Album2/
│   │   └── Artist2/
│   ├── B/
│   ├── -Compilations-/
│   ├── -Splits-/
│   └── -Singles-/
├── Punk & Hardcore/
└── ...
```

Key assumptions:
- Genre folders at top level
- Letter folders (A-Z, #) within genres
- Artist folders within letters
- Album folders with `YYYY - Title` format
- Special collections: `-Compilations-`, `-Splits-`, `-Singles-`

## Dependencies

- Python 3.7+
- Standard library only (no external dependencies)

## Troubleshooting

### "Path not found"
- Verify the path exists
- Use absolute path: `/Volumes/Eksternal/Audio`
- Check permissions

### Slow performance
- Large collections take time to scan
- This is normal - script must check every file
- Consider running overnight for very large collections

### Incorrect statistics
- Check collection structure matches expected format
- Verify album folders use `YYYY - Title` format
- Check for permission issues (some folders may be skipped)

## See Also

- [band_image_scraper.md](band_image_scraper.md) - For filling artwork gaps
- [README.md](README.md) - Overview of all tools
