# Band Image Scraper

Multi-source band image scraper that fetches transparent PNG logos and artist photos from TheAudioDB and Metal Archives. Designed for batch processing and collection maintenance.

## Quick Start

```bash
# Single band
./band_image_scraper.py /Volumes/Eksternal/Audio/Metal/D/Death

# All bands in letter D
./band_image_scraper.py --letter D

# All bands in genre
./band_image_scraper.py --all --genre Metal

# Force re-download
./band_image_scraper.py --letter D --force
```

## Features

- **Transparent PNG logos** from TheAudioDB (primary source)
- **Band photos** from Metal Archives (comprehensive coverage)
- **Smart file checking** - Only downloads missing images
- **Smart band matching** - Disambiguates by discography
- **Batch processing** - By genre, letter, or individual band
- **Progress tracking** - Live statistics during batch operations
- **Rate limiting** - Built-in delays to avoid API blocks

## Usage

### Single Band

```bash
# Process one band folder
./band_image_scraper.py /Volumes/Eksternal/Audio/Metal/D/Death
```

Output:
- `logo.png` - Band logo (transparent PNG if from AudioDB)
- `artist.jpg` - Band/artist photo

### Batch Processing by Letter

```bash
# Process all bands starting with 'D'
./band_image_scraper.py --letter D

# Different genre
./band_image_scraper.py --letter P --genre "Punk & Hardcore"
```

### Batch Processing All Bands

```bash
# Process all bands in Metal genre (warning: takes time!)
./band_image_scraper.py --all

# Different genre
./band_image_scraper.py --all --genre "Hip-Hop"
```

### Force Re-download

```bash
# Re-download even if files exist
./band_image_scraper.py --letter D --force

# Useful for:
# - Upgrading to transparent PNGs
# - Fixing corrupted images
# - Getting higher resolution versions
```

### Verbose Mode

```bash
# Show API calls and matching logic
./band_image_scraper.py --letter D --verbose
```

## Command Line Options

```
positional arguments:
  band_path              Path to specific band folder

optional arguments:
  -h, --help            Show help message and exit
  --base-path PATH      Base path for audio collection
                        (default: /Volumes/Eksternal/Audio)
  --genre GENRE         Genre to process (default: Metal)
  --letter LETTER       Process specific letter (A-Z or #)
  --all                 Process all bands in genre
  --force               Re-download images even if they exist
  --verbose, -v         Verbose output (show API calls)
```

## How It Works

### File Logic

The scraper checks for two files independently:
- **`logo.png`** - Band logo (transparent PNG preferred)
- **`artist.jpg`** - Band/artist photo

**Behavior:**
- If neither exists → Downloads both
- If logo.png exists but not artist.jpg → Downloads only photo
- If artist.jpg exists but not logo.png → Downloads only logo
- If both exist → Skips (unless `--force`)

### Source Priority

1. **Logo Search:**
   - Try TheAudioDB first (transparent PNGs)
   - Fallback to Metal Archives (may have background)

2. **Photo Search:**
   - Only Metal Archives (more comprehensive coverage)

### Band Matching

When multiple bands have the same name, the scraper:
1. Extracts album folder names from your collection (`YYYY - Album Title`)
2. Fetches discography for each candidate from Metal Archives
3. Calculates overlap percentage
4. Uses best match (≥30% threshold)

Example:
```
Your folders:
  1987 - Scream Bloody Gore
  1990 - Spiritual Healing

Death (US) discography:
  ✓ Scream Bloody Gore (1987)
  ✓ Spiritual Healing (1990)

Death (Poland) discography:
  ✗ ...For the Whole World to See (1990)

Result: Matches Death (US) - 100% overlap
```

## Output Files

```
/Volumes/Eksternal/Audio/Metal/D/Death/
├── logo.png         # Transparent PNG (from AudioDB ideally)
├── artist.jpg       # Band photo (from Metal Archives)
└── [album folders]
```

## Statistics

During batch processing, the scraper tracks:
- Processed bands
- Logos downloaded
- Photos downloaded
- Skipped (already complete)
- Failed

Example output:
```
Stats:
  Processed: 45
  Logos downloaded: 38
  Photos downloaded: 42
  Skipped (complete): 12
  Failed: 3
```

## Examples

### Process Letter D

```bash
./band_image_scraper.py --letter D
```

Expected output:
```
📁 Processing letter: D (Metal)
Found 47 bands

[1/47] Processing: Dark Angel
Need: logo photo
⬇ Downloading logo from AudioDB...
✓ Logo saved: /Volumes/Eksternal/Audio/Metal/D/Dark Angel/logo.png
⬇ Downloading photo from Metal Archives...
✓ Photo saved: /Volumes/Eksternal/Audio/Metal/D/Dark Angel/artist.jpg

[2/47] Processing: Death
Need: logo
  AudioDB: Searching for 'Death'
  AudioDB: Found 'Death' with logo
⬇ Downloading logo from AudioDB...
✓ Logo saved: /Volumes/Eksternal/Audio/Metal/D/Death/logo.png

[3/47] ⊘ Decapitated - Already complete
```

### Parallel Processing

```bash
# Process multiple letters simultaneously
for letter in A B C D E; do
  ./band_image_scraper.py --letter $letter &
done
wait
echo "A-E complete!"
```

## Troubleshooting

### "No results found"
- Check exact spelling on Metal Archives
- Try verbose mode: `--verbose`
- Rename folder to match official name

### "Multiple bands found, using first result"
- Script tries discography matching automatically
- Use verbose mode to see which band was selected
- If wrong, rename folder with disambiguation (e.g., "Death (US)")

### Rate Limiting
- Script includes 0.5s delay between bands
- If blocked, wait a few minutes and retry
- Process smaller batches (by letter)

### Images not transparent
- Metal Archives logos may have backgrounds
- AudioDB provides transparent PNGs when available
- Check if AudioDB has the band: `./audiodb_fetcher.py "Band Name" --json`

## API Information

### TheAudioDB
- **Endpoint:** `https://www.theaudiodb.com/api/v1/json/2`
- **Rate Limit:** Generous (free tier)
- **Coverage:** Mainstream + popular underground
- **Best for:** Transparent logos

### Metal Archives
- **Endpoint:** `https://www.metal-archives.com`
- **Rate Limit:** Moderate (script rate-limits itself)
- **Coverage:** Comprehensive (all metal subgenres)
- **Best for:** Photos, obscure bands

## Performance

- **Single band:** ~2-3 seconds
- **Letter (avg 40 bands):** ~3-5 minutes
- **Full Metal genre (1000+ bands):** ~45-60 minutes

Rate limiting is intentional to avoid API blocks.

## Dependencies

- Python 3.7+
- `requests` library
- `beautifulsoup4` library

Install:
```bash
pip3 install requests beautifulsoup4
```

## Integration

Works well with other tools:

```bash
# Step 1: Get comprehensive data from AudioDB
./audiodb_fetcher.py "Death" --download-images /path/to/Death

# Step 2: Fill in missing images
./band_image_scraper.py /path/to/Death

# Result: Complete coverage with best quality images
```

## See Also

- [audiodb_fetcher.md](audiodb_fetcher.md) - For rich band data
- [README.md](README.md) - Overview of all tools
