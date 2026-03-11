# Metal Archives Scraper

Direct scraper for band logos and photos from Metal Archives. Designed for comprehensive metal band coverage, especially underground and obscure bands.

## Quick Start

```bash
# Single band
python3 metal_archives_scraper.py /Volumes/Eksternal/Audio/Metal/D/Death

# All bands in Metal directory
python3 metal_archives_scraper.py --all

# Force re-download
python3 metal_archives_scraper.py --all --force
```

## Features

- **Direct Metal Archives access** - Uses Metal Archives API/search
- **Smart band matching** - Disambiguates by discography
- **Full-sized images** - Downloads full resolution logos and photos
- **Batch processing** - Process all bands in directory
- **Force re-download** - Option to replace existing images

## Usage

### Single Band

```bash
# Process one band folder
python3 metal_archives_scraper.py /Volumes/Eksternal/Audio/Metal/D/Death
```

Output:
- `logo.png` - Band logo (full size)
- `artist.jpg` - Band/artist photo (full size)

### Batch Processing

```bash
# Process all bands in Metal directory
python3 metal_archives_scraper.py --all

# Process specific path
python3 metal_archives_scraper.py --all --path /Volumes/Eksternal/Audio/Metal/D

# Different base path
python3 metal_archives_scraper.py --base-path /Volumes/OtherDrive/Music --all
```

### Force Re-download

```bash
# Re-download even if files exist
python3 metal_archives_scraper.py --all --force
```

## Command Line Options

```
positional arguments:
  band_path              Path to specific band folder

optional arguments:
  -h, --help            Show help message and exit
  --base-path PATH      Base path for audio directory
                        (default: /Volumes/Eksternal/Audio)
  --all                 Process all bands in the Metal directory
  --path PATH           Specific path to process (with --all)
  --force               Re-download images even if they exist
```

## How It Works

### Band Matching

1. Searches Metal Archives by band name
2. If multiple results, extracts album names from your folder
3. Fetches discography for each candidate
4. Matches by comparing album names (≥30% threshold)
5. Uses best match or first result if no good match

### Image Extraction

1. Fetches band page HTML
2. Extracts logo URL using multiple regex patterns
3. Extracts photo URL using multiple methods
4. Removes thumbnail suffixes (`_thumb`, `_small`, `_medium`)
5. Downloads full-sized images

### File Checking

- Checks if `logo.png` and `artist.jpg` exist
- Skips if both exist (unless `--force`)
- Downloads only missing files

## Output Files

```
/Volumes/Eksternal/Audio/Metal/D/Death/
├── logo.png         # Band logo (full size)
├── artist.jpg       # Band photo (full size)
└── [album folders]
```

## Examples

### Process Single Band

```bash
python3 metal_archives_scraper.py /Volumes/Eksternal/Audio/Metal/D/Death
```

Output:
```
============================================================
Processing: Death
Folder: /Volumes/Eksternal/Audio/Metal/D/Death
============================================================
Found 2 albums in folder to match against
Matching against discography for 3 candidates...
Matched by discography: Death
Found band: Death
Band URL: https://www.metal-archives.com/bands/Death/141

Downloading logo from: https://www.metal-archives.com/images/1/4/1/141_logo.jpg
✓ Logo saved successfully: /Volumes/Eksternal/Audio/Metal/D/Death/logo.png

Downloading photo from: https://www.metal-archives.com/images/1/4/1/141_photo.jpg
✓ Photo saved successfully: /Volumes/Eksternal/Audio/Metal/D/Death/artist.jpg
```

### Process All Bands

```bash
python3 metal_archives_scraper.py --all
```

Output:
```
Scanning for band folders in: /Volumes/Eksternal/Audio/Metal

Found 1234 band folders to process

[1/1234]
============================================================
Processing: Dark Angel
...
```

## Troubleshooting

### "No bands found matching"
- Check exact spelling on Metal Archives
- Band may not be in Metal Archives
- Try alternative spellings

### "Metal Archives may be blocking requests"
- Wait a few minutes and retry
- Script uses curl as primary method (more reliable)
- Try processing smaller batches

### "Multiple bands found, using first result"
- Script tries discography matching automatically
- Check which band was selected
- Rename folder with disambiguation if needed

### Images not downloading
- Check network connectivity
- Verify write permissions
- Some bands don't have images on Metal Archives
- Try verbose mode to see errors

## API Information

- **Endpoint:** `https://www.metal-archives.com`
- **Search API:** `https://www.metal-archives.com/search/ajax-band-search/`
- **Rate Limit:** Moderate (script includes delays)
- **Coverage:** Comprehensive (all metal subgenres)
- **Best for:** Underground bands, comprehensive coverage

## Comparison with band_image_scraper.py

| Feature | metal_archives_scraper | band_image_scraper |
|---------|----------------------|-------------------|
| **Sources** | Metal Archives only | AudioDB + Metal Archives |
| **Logo Quality** | Varies (may have background) | Transparent PNG (AudioDB) |
| **Coverage** | Comprehensive metal | Comprehensive + mainstream |
| **Speed** | ~2-3s per band | ~2-3s per band |
| **Use Case** | Metal-only, direct access | Multi-source, best quality |

**Recommendation:** Use `band_image_scraper.py` for most cases (includes AudioDB transparent logos). Use `metal_archives_scraper.py` if you specifically need Metal Archives-only scraping.

## Performance

- **Single band:** ~2-3 seconds
- **All bands (1000+):** ~45-60 minutes

Rate limiting is built-in to avoid API blocks.

## Dependencies

- Python 3.7+
- `requests` library
- `beautifulsoup4` library

Install:
```bash
pip3 install requests beautifulsoup4
```

## See Also

- [band_image_scraper.md](band_image_scraper.md) - Multi-source scraper (recommended)
- [README.md](README.md) - Overview of all tools
