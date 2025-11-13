# Metal Archives Band Image Scraper

A Python tool to scrape full-sized band logos and photos from Metal Archives and save them to your music library folders with automatic background removal for logos.

## Features

- 🎸 Scrapes Metal Archives for band logos and photos
- 📥 Downloads full-sized images
- 🎨 Automatically removes backgrounds from logos (transparent PNG)
- 📁 Saves logos as `logo.png` and photos as `artist.jpg`
- 🔄 Can process individual bands or entire directories
- ⚡ Uses `enmet` library for reliable Metal Archives access (handles anti-scraping measures)

## Installation

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

This will install:
- Core dependencies (requests, beautifulsoup4, Pillow, numpy, scipy, lxml)
- **BiRefNet locally** (transformers, torch, torchvision) - **Recommended: Free, no API key needed!**

2. **Background Removal Options (in priority order):**

   **Option 1: Local BiRefNet (Recommended - Free, No API Key)**
   - Automatically installed with `pip install -r requirements.txt`
   - Uses Hugging Face Transformers to run BiRefNet locally
   - First run will download the model (~500MB), then cached for future use
   - Works with Python 3.14
   - **No API key required!**

   **Option 2: BiRefNet via fal-ai API (Optional - Requires API Key)**
   - Get a free API key from [fal.ai](https://fal.ai/)
   - Set the environment variable:
     ```bash
     export FAL_KEY=your_api_key_here
     ```
   - Falls back to local BiRefNet if API key is not set

   **Option 3: rembg (Optional - Not compatible with Python 3.14)**
   - Only works with Python <3.14
   - Install manually: `pip install rembg`

   **Option 4: PIL Fallback**
   - Basic background removal using PIL
   - Works but lower quality than BiRefNet
   - Automatically used if other methods are unavailable

The script will automatically use the best available method in this priority order.

## Usage

### Process a specific band

```bash
python metal_archives_scraper.py /Volumes/Eksternal/Audio/Metal/D/Diabolic
```

### Process all bands in Metal directory

```bash
python metal_archives_scraper.py --all
```

### Use a different base path

```bash
python metal_archives_scraper.py --base-path /Volumes/Eksternal/Audio --all
```

## Directory Structure

The script expects your music library to be organized like:

```
/Volumes/Eksternal/Audio/
└── Metal/
    └── D/
        └── Diabolic/
            ├── logo.png      (created by script)
            └── artist.jpg    (created by script)
```

## How It Works

1. **Band Search**: Searches Metal Archives for the band (handles duplicate names by matching discography)
2. **Image Extraction**: Fetches the band page and extracts full-sized logo and photo URLs
3. **Download**: Downloads images to the band's folder
4. **Background Removal**: Removes backgrounds from logos using BiRefNet (local or API), rembg, or PIL fallback
5. **Save**: Saves logo as `logo.png` (transparent) and photo as `artist.jpg`

## Dependencies

- **transformers, torch, torchvision**: For local BiRefNet background removal (recommended, free)
- **fal-client**: Optional - for BiRefNet via fal-ai API (requires API key)
- **rembg**: Optional - AI-powered background removal (not compatible with Python 3.14)
- **Pillow**: Image processing (fallback for background removal)
- **requests**: HTTP requests
- **beautifulsoup4**: HTML parsing
- **numpy, scipy**: Advanced image processing

## Notes

- The script will skip bands that already have both `logo.png` and `artist.jpg`
- If `rembg` is not available, it falls back to basic PIL background removal
- Metal Archives may have rate limiting or anti-scraping measures - the script includes appropriate delays and headers
- If you encounter 403 Forbidden errors, Metal Archives may be blocking automated requests. Try:
  - Waiting a few minutes and trying again
  - Using a VPN or different network
  - Running the script at different times
- Always respect Metal Archives' terms of service

## Troubleshooting

### "JSONDecodeError" or blocking errors
If you see errors about empty responses or JSON decode errors, Metal Archives may be temporarily blocking requests:
- Wait a few minutes and try again (rate limiting may be temporary)
- Use a VPN or different network (IP may be blocked)
- Try running at different times
- Metal Archives may have server issues - try again later

The script uses `enmet` which handles anti-scraping measures better than direct scraping, but temporary blocking can still occur.

### "No bands found"
- Check the band name spelling
- Some bands may not be in Metal Archives
- Try using the exact band name as it appears on Metal Archives

### Background removal not working
- **For best results**: Install transformers and torch for local BiRefNet:
  ```bash
  pip install transformers torch torchvision
  ```
- First run will download the BiRefNet model (~500MB) - this is normal
- If local BiRefNet fails, the script will try fal-ai API (if FAL_KEY is set), then rembg, then PIL
- The PIL fallback method is basic and may not work well for all logos

## License

This tool is for personal use. Please respect Metal Archives' terms of service.

