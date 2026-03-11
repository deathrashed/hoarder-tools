# AudioDB Fetcher

Comprehensive band data fetcher from TheAudioDB API. Fetches complete artist profiles including biographies, metadata, social links, and all available images.

## Quick Start

```bash
# Fetch and display data
./audiodb_fetcher.py "Death"

# Save as markdown
./audiodb_fetcher.py "Death" --output death.md

# Download all images
./audiodb_fetcher.py "Death" --download-images /path/to/band/folder

# JSON output
./audiodb_fetcher.py "Death" --json
```

## Features

- **Complete artist profiles** - Formation dates, location, label, members
- **Multi-language biographies** - English, German, French, Spanish, Italian, Portuguese
- **All available images** - Logos, photos, fanart, banners, cutouts
- **Social media links** - Website, Facebook, Twitter
- **MusicBrainz integration** - MusicBrainz ID for cross-referencing
- **Obsidian-ready markdown** - YAML frontmatter, formatted content
- **JSON output** - Structured data for scripting

## Usage

### Basic Usage

```bash
# Display artist info in terminal
./audiodb_fetcher.py "Slayer"

# Save to file
./audiodb_fetcher.py "Slayer" --output slayer.md
```

### Download Images

```bash
# Download all available images to band folder
./audiodb_fetcher.py "Death" \
  --download-images /Volumes/Eksternal/Audio/Metal/D/Death

# Images downloaded:
# - logo.png (transparent PNG)
# - artist.jpg
# - artist_wide.jpg
# - fanart1.jpg through fanart4.jpg
# - banner.jpg
# - cutout.png (if available)
# - clearart.png (if available)
```

### JSON Output

```bash
# Output as JSON
./audiodb_fetcher.py "Death" --json

# Save JSON to file
./audiodb_fetcher.py "Death" --json --output death.json

# Use in scripts
./audiodb_fetcher.py "Death" --json | jq '.metadata.formed'
```

### Verbose Mode

```bash
# Show API calls and download progress
./audiodb_fetcher.py "Death" --download-images ./Death --verbose
```

### Raw API Response

```bash
# See raw API response (debugging)
./audiodb_fetcher.py "Death" --raw
```

## Command Line Options

```
positional arguments:
  artist                Artist/band name to search

optional arguments:
  -h, --help            Show help message and exit
  --output, -o FILE     Save markdown/JSON to file
  --download-images DIR Download all images to directory
  --json                Output as JSON instead of markdown
  --raw                 Show raw API response (debugging)
  --verbose, -v         Verbose output (show API calls, downloads)
```

## Output Formats

### Markdown Format

The markdown output includes:
- YAML frontmatter with metadata
- Overview section with key information
- Links section (website, social media, MusicBrainz)
- Biography (English, with other languages in collapsible sections)
- Images section with links to all available images

Example:
```markdown
---
artist: "Death"
genre: "Death Metal"
style: "Metal"
formed: 1984
status: disbanded
label: "Relapse Records"
location: "Orlando, Florida, USA"
members: 4
musicbrainz_id: "dbb3b771-ae77-4381-b61c-758b5b7898ec"
source: "TheAudioDB"
fetched: 2026-01-07
---

# Death

## Overview

**Genre:** Death Metal / Metal
**Active:** 1984 (disbanded)
**Location:** Orlando, Florida, USA
...
```

### JSON Format

Structured JSON with organized sections:
- `artist` - Artist name
- `metadata` - Formation, location, members, label
- `genre` - Style, genre, mood
- `links` - Website, social media, MusicBrainz ID
- `biographies` - All language versions
- `images` - All image URLs
- `raw` - Complete API response

## Integration Examples

### Obsidian Workflow

```bash
VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian/Research/Music"

# Create band note
./audiodb_fetcher.py "Death" \
  --output "$VAULT/Death Metal/Death.md" \
  --download-images /Volumes/Eksternal/Audio/Metal/D/Death
```

### Batch Processing

```bash
# Process multiple bands
for band in "Death" "Morbid Angel" "Obituary"; do
  ./audiodb_fetcher.py "$band" \
    --output "bands/${band}.md" \
    --download-images "/Volumes/Eksternal/Audio/Metal/${band:0:1}/$band"
  sleep 1  # Rate limiting
done
```

### Script Integration

```python
#!/usr/bin/env python3
import subprocess
import json

result = subprocess.run(
    ['./audiodb_fetcher.py', 'Death', '--json'],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)
print(f"Artist: {data['artist']}")
print(f"Formed: {data['metadata']['formed']}")
print(f"Genre: {data['genre']['genre']}")
```

## API Information

- **Endpoint:** `https://www.theaudiodb.com/api/v1/json/2/search.php?s=ARTIST_NAME`
- **Rate Limit:** Generous (free tier, no API key required)
- **Recommended delay:** 0.5-1s between requests
- **Coverage:** Mainstream + popular underground bands

## Troubleshooting

### "Artist not found"
- Check exact spelling on TheAudioDB website
- Some bands not in database (especially new/underground)
- Try alternative spellings or variations

### Images not downloading
- Check network connectivity
- Verify write permissions on target directory
- Some bands have limited image coverage
- Use `--verbose` to see which images failed

### Rate limiting
- Script includes delays between requests
- If blocked, wait a few minutes and retry
- Process smaller batches

## Performance

- **Single band fetch:** ~1-2 seconds
- **With image downloads:** ~5-10 seconds (10+ images)
- **Batch processing:** Add 1s delay between requests

## Dependencies

- Python 3.7+
- `requests` library

Install:
```bash
pip3 install requests
```

## See Also

- [band_image_scraper.md](band_image_scraper.md) - For batch image downloads
- [README.md](README.md) - Overview of all tools
