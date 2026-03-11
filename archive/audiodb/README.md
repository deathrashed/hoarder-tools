# AudioDB Tools - Music Collection Management

A comprehensive toolkit for managing and enriching your music collection with metadata, images, and documentation from multiple sources.

## Overview

This folder contains Python scripts for:
- Fetching comprehensive band data from TheAudioDB
- Scraping band logos and photos from multiple sources
- Generating collection statistics
- Managing band images and metadata

## Scripts

### 1. `audiodb_fetcher.py`
**Purpose:** Fetch comprehensive band data from TheAudioDB API  
**Best for:** Research, documentation, rich metadata  
**Output:** Markdown (Obsidian-ready) or JSON

Fetches complete artist profiles including:
- Multi-language biographies
- Formation/disbanded dates
- Genre and style information
- Social media links
- MusicBrainz IDs
- All available images (logos, photos, fanart, banners)

**Quick Start:**
```bash
# Fetch data for a band
./audiodb_fetcher.py "Death" --output death.md

# Download all images
./audiodb_fetcher.py "Death" --download-images /path/to/band/folder

# JSON output
./audiodb_fetcher.py "Death" --json
```

**Documentation:** See [audiodb_fetcher.md](audiodb_fetcher.md)

---

### 2. `band_image_scraper.py`
**Purpose:** Batch download band logos and photos  
**Best for:** Collection maintenance, bulk operations  
**Output:** `logo.png` and `artist.jpg` in band folders

Multi-source scraper that:
- Fetches transparent PNG logos from TheAudioDB
- Falls back to Metal Archives for comprehensive coverage
- Smart band matching by discography
- Independent file checking (only downloads missing images)
- Batch processing by genre, letter, or individual band

**Quick Start:**
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

**Documentation:** See [band_image_scraper.md](band_image_scraper.md)

---

### 3. `collection_stats.py`
**Purpose:** Generate comprehensive collection statistics  
**Best for:** Collection analysis, maintenance tracking  
**Output:** `stats.json` and `STATS.md`

Analyzes your entire music collection and generates:
- Artist/album/track counts by genre
- Storage usage statistics
- Audio format distribution
- Albums by decade
- Artwork coverage (covers, logos)
- Documentation coverage (info files, markdown)
- Special collections (compilations, splits, singles)

**Quick Start:**
```bash
# Default path (/Volumes/Eksternal/Audio)
python3 collection_stats.py

# Custom path
python3 collection_stats.py /path/to/Audio
```

**Documentation:** See [collection_stats.md](collection_stats.md)

---

### 4. `metal_archives_scraper.py`
**Purpose:** Scrape band logos and photos from Metal Archives  
**Best for:** Underground bands, comprehensive metal coverage  
**Output:** `logo.png` and `artist.jpg` in band folders

Direct Metal Archives scraper with:
- Smart band matching by discography
- Full-sized image downloads
- Batch processing support
- Force re-download option

**Quick Start:**
```bash
# Single band
python3 metal_archives_scraper.py /Volumes/Eksternal/Audio/Metal/D/Death

# All bands
python3 metal_archives_scraper.py --all

# Force re-download
python3 metal_archives_scraper.py --all --force
```

**Note:** `band_image_scraper.py` includes Metal Archives functionality with additional AudioDB support. Use `metal_archives_scraper.py` if you specifically need Metal Archives-only scraping.

**Documentation:** See [metal_archives_scraper.md](metal_archives_scraper.md)

---

## Installation

### Requirements

All scripts require Python 3.7+ and the following packages:

```bash
pip3 install requests beautifulsoup4 Pillow
```

### Setup

1. Ensure scripts are executable:
```bash
chmod +x *.py
```

2. Test installation:
```bash
./audiodb_fetcher.py "Slayer" --json | head -20
```

---

## Common Workflows

### Workflow 1: New Band Documentation

```bash
BAND="Death"
COLLECTION="/Volumes/Eksternal/Audio/Metal/D/$BAND"
OBSIDIAN="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian/Research/Music/Death Metal"

# Step 1: Get comprehensive data + images
./audiodb_fetcher.py "$BAND" \
  --output "$OBSIDIAN/${BAND}.md" \
  --download-images "$COLLECTION"

# Step 2: Fill in missing images from Metal Archives
./band_image_scraper.py "$COLLECTION"
```

### Workflow 2: Batch Process Letter

```bash
# Process all bands in letter D
./band_image_scraper.py --letter D

# Or with AudioDB data
cd /Volumes/Eksternal/Audio/Metal/D
for band_dir in */; do
  band="${band_dir%/}"
  ./audiodb_fetcher.py "$band" --download-images "$band_dir" 2>/dev/null || true
  ./band_image_scraper.py "$band_dir"
  sleep 1
done
```

### Workflow 3: Collection Maintenance

```bash
# Generate statistics
python3 collection_stats.py

# Fill in missing images
./band_image_scraper.py --letter D

# Check coverage
find /Volumes/Eksternal/Audio/Metal/D -name "logo.png" | wc -l
```

---

## Tool Comparison

| Feature | audiodb_fetcher | band_image_scraper | collection_stats |
|---------|----------------|-------------------|------------------|
| **Purpose** | Rich data | Images | Statistics |
| **Logo Quality** | ✓ Transparent PNG | ~ Varies | N/A |
| **Biography** | ✓ 7 languages | ✗ No | N/A |
| **Batch Mode** | Manual loop | ✓ Built-in | N/A |
| **Coverage** | Mainstream | Comprehensive | N/A |
| **Speed** | 1-2s/band | 2-3s/band | 5-10min/full |

---

## File Structure

```
audiodb/
├── README.md                    # This file
├── audiodb_fetcher.py          # AudioDB data fetcher
├── audiodb_fetcher.md          # AudioDB fetcher documentation
├── band_image_scraper.py        # Multi-source image scraper
├── band_image_scraper.md       # Image scraper documentation
├── collection_stats.py         # Collection statistics generator
├── collection_stats.md         # Statistics documentation
├── metal_archives_scraper.py   # Metal Archives scraper
└── metal_archives_scraper.md   # Metal Archives documentation
```

---

## API Information

### TheAudioDB
- **Endpoint:** `https://www.theaudiodb.com/api/v1/json/2`
- **Rate Limit:** Generous (free tier, no API key)
- **Coverage:** Mainstream + popular underground
- **Best for:** Transparent logos, rich metadata

### Metal Archives
- **Endpoint:** `https://www.metal-archives.com`
- **Rate Limit:** Moderate (scripts include rate limiting)
- **Coverage:** Comprehensive (all metal subgenres)
- **Best for:** Photos, obscure bands, encyclopedic coverage

---

## Troubleshooting

### "Artist not found"
- Try exact spelling from AudioDB/Metal Archives
- Some bands not in databases (especially new/underground)
- Use verbose mode: `--verbose` to see search queries

### Rate Limiting
- Scripts include built-in delays (0.5-1s between requests)
- If blocked, wait a few minutes and retry
- Process smaller batches (by letter instead of --all)

### Images not downloading
- Check network connectivity
- Verify write permissions on target directory
- Some bands have limited image coverage
- Try `--verbose` to see which images failed

### Wrong band matched
- Scripts try discography matching automatically
- Use verbose mode to see which band was selected
- Rename folder with disambiguation if needed (e.g., "Death (US)")

---

## Performance

- **Single band (audiodb_fetcher):** ~1-2 seconds
- **Single band (band_image_scraper):** ~2-3 seconds
- **Letter (avg 40 bands):** ~3-5 minutes
- **Full genre (1000+ bands):** ~45-60 minutes
- **Collection stats:** 5-10 minutes (depends on collection size)

---

## Integration

These tools are designed to work together:

1. **AudioDB Fetcher** → Rich data + images
2. **Band Image Scraper** → Fill gaps, batch processing
3. **Collection Stats** → Track coverage and completeness

**Recommended workflow:**
- Use AudioDB Fetcher for research/documentation
- Use Band Image Scraper for collection maintenance
- Use Collection Stats to track progress

---

## License

Part of personal music collection tools. Use freely, modify as needed.

---

## Credits

- **TheAudioDB:** Comprehensive music database API
- **Metal Archives:** Encyclopedic metal database
- **You:** For building this meticulously organized collection

---

**Last Updated:** January 2026  
**Location:** `/Users/rd/.config/tools/hoarder-tools/audiodb`
