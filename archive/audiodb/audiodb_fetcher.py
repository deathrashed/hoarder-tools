#!/usr/bin/env python3
"""
AudioDB Comprehensive Data Fetcher with Batch Processing
==========================================================
Fetches data from TheAudioDB for bands and downloads images (logo.png, artist.jpg).

Features:
- Single band or batch processing (by letter, genre, or all)
- Transparent PNG logos from AudioDB
- Artist photos
- Interactive mode for easy use
- Smart file checking (only downloads missing images)

Usage:
    # Single band
    ./audiodb_fetcher.py "Death"
    
    # Single band - download images only
    ./audiodb_fetcher.py --band-folder /Volumes/Eksternal/Audio/Metal/D/Death
    
    # All bands in letter D
    ./audiodb_fetcher.py --letter D
    
    # All bands in genre
    ./audiodb_fetcher.py --all --genre Metal
    
    # Interactive mode
    ./audiodb_fetcher.py --interactive
"""

import os
import sys
import argparse
import json
import requests
import time
import re
from pathlib import Path
from urllib.parse import quote
from datetime import datetime

AUDIODB_API_BASE = "https://www.theaudiodb.com/api/v1/json/2"
DEFAULT_BASE_PATH = "/Volumes/Eksternal/Audio"


class AudioDBFetcher:
    """Comprehensive AudioDB data fetcher with batch processing."""
    
    def __init__(self, base_path=DEFAULT_BASE_PATH, verbose=False):
        self.base_path = Path(base_path)
        self.verbose = verbose
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        })
        self.stats = {
            'processed': 0,
            'logos_downloaded': 0,
            'photos_downloaded': 0,
            'skipped': 0,
            'failed': 0
        }
    
    def search_artist(self, artist_name):
        """Search for artist and return complete data."""
        try:
            search_url = f"{AUDIODB_API_BASE}/search.php?s={quote(artist_name)}"
            
            if self.verbose:
                print(f"  Searching: {search_url}")
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            artists = data.get('artists')
            
            if not artists or len(artists) == 0:
                return None
            
            # Return first result (usually best match)
            return artists[0]
            
        except Exception as e:
            if self.verbose:
                print(f"  Error: {e}")
            return None
    
    def download_image(self, url, output_path):
        """Download an image from URL."""
        try:
            if not url:
                return False
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if self.verbose:
                print(f"    Downloading: {output_path.name}")
            
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"    Failed: {e}")
            return False
    
    def download_key_images(self, artist_data, output_dir, force=False):
        """Download key images: logo.png and artist.jpg."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logo_path = output_dir / 'logo.png'
        photo_path = output_dir / 'artist.jpg'
        
        downloaded = []
        skipped = []
        
        # Download logo (transparent PNG from AudioDB)
        logo_url = artist_data.get('strArtistLogo')
        if logo_url:
            if force or not logo_path.exists():
                if self.download_image(logo_url, logo_path):
                    downloaded.append('logo.png')
                    self.stats['logos_downloaded'] += 1
                else:
                    skipped.append('logo.png')
            else:
                skipped.append('logo.png (exists)')
        else:
            skipped.append('logo.png (not available)')
        
        # Download artist photo
        photo_url = artist_data.get('strArtistThumb')
        if photo_url:
            if force or not photo_path.exists():
                if self.download_image(photo_url, photo_path):
                    downloaded.append('artist.jpg')
                    self.stats['photos_downloaded'] += 1
                else:
                    skipped.append('artist.jpg')
            else:
                skipped.append('artist.jpg (exists)')
        else:
            skipped.append('artist.jpg (not available)')
        
        return downloaded, skipped
    
    def process_band(self, band_folder_path, force=False, images_only=False):
        """Process a single band folder."""
        band_folder = Path(band_folder_path)
        
        if not band_folder.exists():
            print(f"✗ Folder not found: {band_folder}")
            return False
        
        band_name = band_folder.name
        
        # Check what's needed
        logo_path = band_folder / 'logo.png'
        photo_path = band_folder / 'artist.jpg'
        
        need_logo = force or not logo_path.exists()
        need_photo = force or not photo_path.exists()
        
        if not need_logo and not need_photo and not images_only:
            print(f"⊘ {band_name} - Already complete")
            self.stats['skipped'] += 1
            return True
        
        if images_only and not need_logo and not need_photo:
            print(f"⊘ {band_name} - Images already exist")
            self.stats['skipped'] += 1
            return True
        
        print(f"\n{'='*60}")
        print(f"Processing: {band_name}")
        if images_only:
            print(f"Need: {' logo' if need_logo else ''}{' photo' if need_photo else ''}")
        print(f"{'='*60}")
        
        self.stats['processed'] += 1
        success = True
        
        # Search AudioDB
        artist_data = self.search_artist(band_name)
        
        if not artist_data:
            print(f"✗ Artist not found in TheAudioDB")
            self.stats['failed'] += 1
            return False
        
        artist_name = artist_data.get('strArtist', band_name)
        print(f"✓ Found: {artist_name}")
        
        # Download key images
        if need_logo or need_photo or images_only:
            downloaded, skipped = self.download_key_images(artist_data, band_folder, force=force)
            if downloaded:
                print(f"✓ Downloaded: {', '.join(downloaded)}")
            if skipped and self.verbose:
                print(f"⊘ Skipped: {', '.join(skipped)}")
        
        if not success:
            self.stats['failed'] += 1
        
        return success
    
    def find_band_folders(self, path):
        """Find all band folders in a directory tree."""
        path = Path(path)
        band_folders = []
        
        # A band folder has album subdirectories (YYYY - Album format)
        for item in path.iterdir():
            if not item.is_dir() or item.name.startswith('.'):
                continue
            
            # Check if has album subdirectories
            has_albums = any(
                subitem.is_dir() and 
                re.match(r'^\d{4}\s*-\s*.+', subitem.name)
                for subitem in item.iterdir()
            )
            
            if has_albums:
                band_folders.append(item)
        
        return band_folders
    
    def process_letter(self, letter, genre="Metal", force=False, images_only=True):
        """Process all bands in a letter folder."""
        letter_path = self.base_path / genre / letter.upper()
        
        if not letter_path.exists():
            print(f"✗ Letter folder not found: {letter_path}")
            return
        
        print(f"\n📁 Processing letter: {letter.upper()} ({genre})")
        print(f"Path: {letter_path}\n")
        
        band_folders = self.find_band_folders(letter_path)
        
        if not band_folders:
            print("No band folders found.")
            return
        
        print(f"Found {len(band_folders)} bands\n")
        
        for i, folder in enumerate(band_folders, 1):
            print(f"[{i}/{len(band_folders)}]", end=" ")
            self.process_band(folder, force=force, images_only=images_only)
            time.sleep(0.5)  # Rate limiting
        
        self.print_stats()
    
    def process_all(self, genre="Metal", force=False, images_only=True):
        """Process all bands in a genre."""
        genre_path = self.base_path / genre
        
        if not genre_path.exists():
            print(f"✗ Genre folder not found: {genre_path}")
            return
        
        print(f"\n📚 Processing all bands in: {genre}")
        print(f"Path: {genre_path}\n")
        
        # Find all letter directories
        letters = []
        for item in genre_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('-'):
                # Letter directory (A-Z, #) or special (Compilations, etc)
                if len(item.name) <= 2 or item.name == '#':
                    letters.append(item.name)
        
        letters.sort()
        
        for letter in letters:
            self.process_letter(letter, genre=genre, force=force, images_only=images_only)
            print()
        
        print("\n" + "="*60)
        print("FINAL STATISTICS")
        print("="*60)
        self.print_stats()
    
    def print_stats(self):
        """Print statistics."""
        print(f"\nStats:")
        print(f"  Processed: {self.stats['processed']}")
        print(f"  Logos downloaded: {self.stats['logos_downloaded']}")
        print(f"  Photos downloaded: {self.stats['photos_downloaded']}")
        print(f"  Skipped (complete): {self.stats['skipped']}")
        print(f"  Failed: {self.stats['failed']}")
    
    # Legacy methods for backward compatibility
    def download_all_images(self, artist_data, output_dir):
        """Download all available images (legacy method)."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        images = {
            'logo.png': artist_data.get('strArtistLogo'),
            'artist.jpg': artist_data.get('strArtistThumb'),
            'artist_wide.jpg': artist_data.get('strArtistWideThumb'),
            'fanart1.jpg': artist_data.get('strArtistFanart'),
            'fanart2.jpg': artist_data.get('strArtistFanart2'),
            'fanart3.jpg': artist_data.get('strArtistFanart3'),
            'fanart4.jpg': artist_data.get('strArtistFanart4'),
            'banner.jpg': artist_data.get('strArtistBanner'),
            'cutout.png': artist_data.get('strArtistCutout'),
            'clearart.png': artist_data.get('strArtistClearart'),
        }
        
        downloaded = []
        skipped = []
        
        for filename, url in images.items():
            if url:
                output_path = output_dir / filename
                if self.download_image(url, output_path):
                    downloaded.append(filename)
                else:
                    skipped.append(filename)
            else:
                skipped.append(f"{filename} (not available)")
        
        return downloaded, skipped
    
    def format_markdown(self, artist_data):
        """Format artist data as Obsidian-ready markdown."""
        if not artist_data:
            return None
        
        # Extract data with fallbacks
        name = artist_data.get('strArtist', 'Unknown Artist')
        genre = artist_data.get('strGenre', '')
        style = artist_data.get('strStyle', '')
        formed = artist_data.get('intFormedYear', '')
        disbanded = artist_data.get('strDisbanded', 'No')
        label = artist_data.get('strLabel', '')
        location = artist_data.get('strCountry', '')
        members = artist_data.get('intMembers', '')
        website = artist_data.get('strWebsite', '')
        facebook = artist_data.get('strFacebook', '')
        twitter = artist_data.get('strTwitter', '')
        musicbrainz = artist_data.get('strMusicBrainzID', '')
        
        # Biography (prefer English)
        bio_en = artist_data.get('strBiographyEN', '')
        bio_de = artist_data.get('strBiographyDE', '')
        bio_fr = artist_data.get('strBiographyFR', '')
        
        # Build markdown
        md = []
        
        # YAML frontmatter
        md.append('---')
        md.append(f'artist: "{name}"')
        if genre:
            md.append(f'genre: "{genre}"')
        if style:
            md.append(f'style: "{style}"')
        if formed:
            md.append(f'formed: {formed}')
        if disbanded == 'Yes':
            md.append(f'status: disbanded')
        else:
            md.append(f'status: active')
        if label:
            md.append(f'label: "{label}"')
        if location:
            md.append(f'location: "{location}"')
        if members:
            md.append(f'members: {members}')
        if musicbrainz:
            md.append(f'musicbrainz_id: "{musicbrainz}"')
        md.append(f'source: "TheAudioDB"')
        md.append(f'fetched: {datetime.now().strftime("%Y-%m-%d")}')
        md.append('---')
        md.append('')
        
        # Title
        md.append(f'# {name}')
        md.append('')
        
        # Quick Info Box
        md.append('## Overview')
        md.append('')
        if genre or style:
            md.append(f'**Genre:** {genre} / {style}')
        if formed:
            if disbanded == 'Yes':
                md.append(f'**Active:** {formed} (disbanded)')
            else:
                md.append(f'**Formed:** {formed}')
        if location:
            md.append(f'**Location:** {location}')
        if label:
            md.append(f'**Label:** {label}')
        if members:
            md.append(f'**Members:** {members}')
        md.append('')
        
        # Links
        links = []
        if website:
            links.append(f'[Official Website](https://{website})')
        if facebook:
            links.append(f'[Facebook](https://{facebook})')
        if twitter and twitter != '1':  # '1' is a placeholder
            links.append(f'[Twitter](https://twitter.com/{twitter})')
        if musicbrainz:
            links.append(f'[MusicBrainz](https://musicbrainz.org/artist/{musicbrainz})')
        
        if links:
            md.append('## Links')
            md.append('')
            md.append(' • '.join(links))
            md.append('')
        
        # Biography (English)
        if bio_en:
            md.append('## Biography')
            md.append('')
            # Split into paragraphs
            paragraphs = bio_en.split('\\n')
            for para in paragraphs:
                if para.strip():
                    md.append(para.strip())
                    md.append('')
        
        # Additional Biographies
        other_bios = []
        if bio_de:
            other_bios.append(('German', bio_de))
        if bio_fr:
            other_bios.append(('French', bio_fr))
        
        if other_bios:
            md.append('## Biographies (Other Languages)')
            md.append('')
            for lang, bio in other_bios:
                md.append(f'### {lang}')
                md.append('')
                md.append('<details>')
                md.append(f'<summary>View {lang} biography</summary>')
                md.append('')
                paragraphs = bio.split('\\n')
                for para in paragraphs:
                    if para.strip():
                        md.append(para.strip())
                        md.append('')
                md.append('</details>')
                md.append('')
        
        # Images section
        md.append('## Images')
        md.append('')
        
        images = []
        if artist_data.get('strArtistLogo'):
            images.append(('Logo', artist_data['strArtistLogo']))
        if artist_data.get('strArtistThumb'):
            images.append(('Artist Photo', artist_data['strArtistThumb']))
        if artist_data.get('strArtistWideThumb'):
            images.append(('Wide Photo', artist_data['strArtistWideThumb']))
        if artist_data.get('strArtistBanner'):
            images.append(('Banner', artist_data['strArtistBanner']))
        
        fanarts = [
            artist_data.get('strArtistFanart'),
            artist_data.get('strArtistFanart2'),
            artist_data.get('strArtistFanart3'),
            artist_data.get('strArtistFanart4'),
        ]
        fanarts = [f for f in fanarts if f]
        
        if images:
            for label, url in images:
                md.append(f'**{label}:** [View]({url})')
        
        if fanarts:
            md.append('')
            md.append(f'**Fanart:** {len(fanarts)} images available')
            for i, url in enumerate(fanarts, 1):
                md.append(f'- [Fanart {i}]({url})')
        
        md.append('')
        
        # Footer
        md.append('---')
        md.append('')
        md.append(f'*Data sourced from [TheAudioDB](https://www.theaudiodb.com) on {datetime.now().strftime("%Y-%m-%d")}*')
        
        return '\n'.join(md)
    
    def format_json(self, artist_data):
        """Format artist data as JSON."""
        if not artist_data:
            return None
        
        # Clean up the data (remove nulls, organize)
        cleaned = {
            'artist': artist_data.get('strArtist'),
            'metadata': {
                'formed': artist_data.get('intFormedYear'),
                'disbanded': artist_data.get('strDisbanded') == 'Yes',
                'location': artist_data.get('strCountry'),
                'members': artist_data.get('intMembers'),
                'label': artist_data.get('strLabel'),
            },
            'genre': {
                'style': artist_data.get('strStyle'),
                'genre': artist_data.get('strGenre'),
                'mood': artist_data.get('strMood'),
            },
            'links': {
                'website': artist_data.get('strWebsite'),
                'facebook': artist_data.get('strFacebook'),
                'twitter': artist_data.get('strTwitter') if artist_data.get('strTwitter') != '1' else None,
                'musicbrainz_id': artist_data.get('strMusicBrainzID'),
            },
            'biographies': {
                'english': artist_data.get('strBiographyEN'),
                'german': artist_data.get('strBiographyDE'),
                'french': artist_data.get('strBiographyFR'),
                'spanish': artist_data.get('strBiographyES'),
                'italian': artist_data.get('strBiographyIT'),
                'portuguese': artist_data.get('strBiographyPT'),
            },
            'images': {
                'logo': artist_data.get('strArtistLogo'),
                'thumb': artist_data.get('strArtistThumb'),
                'wide_thumb': artist_data.get('strArtistWideThumb'),
                'banner': artist_data.get('strArtistBanner'),
                'cutout': artist_data.get('strArtistCutout'),
                'clearart': artist_data.get('strArtistClearart'),
                'fanart': [
                    artist_data.get('strArtistFanart'),
                    artist_data.get('strArtistFanart2'),
                    artist_data.get('strArtistFanart3'),
                    artist_data.get('strArtistFanart4'),
                ],
            },
            'raw': artist_data,
        }
        
        # Remove None values
        def remove_nones(obj):
            if isinstance(obj, dict):
                return {k: remove_nones(v) for k, v in obj.items() if v is not None and v != ''}
            elif isinstance(obj, list):
                return [remove_nones(item) for item in obj if item is not None and item != '']
            else:
                return obj
        
        return remove_nones(cleaned)


def interactive_mode():
    """Interactive mode for easy use."""
    print("\n" + "="*60)
    print("AudioDB Fetcher - Interactive Mode")
    print("="*60)
    print()
    
    base_path = input(f"Base path [{DEFAULT_BASE_PATH}]: ").strip()
    if not base_path:
        base_path = DEFAULT_BASE_PATH
    
    print("\nWhat would you like to do?")
    print("1. Single band folder")
    print("2. All bands in a letter")
    print("3. All bands in a genre")
    print("4. Search for band data (no batch)")
    
    choice = input("\nChoice [1-4]: ").strip()
    
    fetcher = AudioDBFetcher(base_path=base_path, verbose=True)
    
    if choice == '1':
        band_path = input("Band folder path: ").strip()
        force = input("Force re-download? [y/N]: ").strip().lower() == 'y'
        fetcher.process_band(band_path, force=force, images_only=True)
    
    elif choice == '2':
        genre = input("Genre [Metal]: ").strip() or "Metal"
        letter = input("Letter (A-Z or #): ").strip().upper()
        force = input("Force re-download? [y/N]: ").strip().lower() == 'y'
        fetcher.process_letter(letter, genre=genre, force=force, images_only=True)
    
    elif choice == '3':
        genre = input("Genre [Metal]: ").strip() or "Metal"
        force = input("Force re-download? [y/N]: ").strip().lower() == 'y'
        confirm = input(f"Process ALL bands in {genre}? This may take a while. [y/N]: ").strip().lower()
        if confirm == 'y':
            fetcher.process_all(genre=genre, force=force, images_only=True)
        else:
            print("Cancelled.")
    
    elif choice == '4':
        artist = input("Band name: ").strip()
        output = input("Save markdown to file (optional): ").strip()
        download = input("Download images to folder (optional): ").strip()
        
        artist_data = fetcher.search_artist(artist)
        if artist_data:
            if download:
                fetcher.download_key_images(artist_data, download)
            if output:
                markdown = fetcher.format_markdown(artist_data)
                with open(output, 'w') as f:
                    f.write(markdown)
                print(f"✓ Saved to {output}")
            else:
                print(fetcher.format_markdown(artist_data))
        else:
            print("✗ Artist not found")
    
    else:
        print("Invalid choice")


def main():
    parser = argparse.ArgumentParser(
        description='Fetch data from TheAudioDB with batch processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single band (search and display)
  %(prog)s "Death"
  
  # Single band folder (download images)
  %(prog)s --band-folder /Volumes/Eksternal/Audio/Metal/D/Death
  
  # All bands in letter D
  %(prog)s --letter D
  
  # All bands in genre
  %(prog)s --all --genre Metal
  
  # Interactive mode
  %(prog)s --interactive
  
  # Legacy: Download all images
  %(prog)s "Death" --download-images /path/to/folder
        """
    )
    
    parser.add_argument(
        'artist',
        nargs='?',
        help='Artist/band name to search (legacy mode)'
    )
    parser.add_argument(
        '--band-folder',
        metavar='PATH',
        help='Process single band folder (download logo.png and artist.jpg)'
    )
    parser.add_argument(
        '--base-path',
        default=DEFAULT_BASE_PATH,
        help=f'Base path for audio collection (default: {DEFAULT_BASE_PATH})'
    )
    parser.add_argument(
        '--genre',
        default='Metal',
        help='Genre to process (default: Metal)'
    )
    parser.add_argument(
        '--letter',
        help='Process specific letter (A-Z or #)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all bands in genre'
    )
    parser.add_argument(
        '--output', '-o',
        help='Save markdown to file (legacy mode)'
    )
    parser.add_argument(
        '--download-images',
        metavar='DIR',
        help='Download all images to directory (legacy mode)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON instead of markdown (legacy mode)'
    )
    parser.add_argument(
        '--raw',
        action='store_true',
        help='Show raw API response (legacy mode)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Re-download images even if they exist'
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Interactive mode'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Interactive mode
    if args.interactive:
        interactive_mode()
        return
    
    fetcher = AudioDBFetcher(base_path=args.base_path, verbose=args.verbose)
    
    # Batch processing modes
    if args.band_folder:
        fetcher.process_band(args.band_folder, force=args.force, images_only=True)
    elif args.letter:
        fetcher.process_letter(args.letter, genre=args.genre, force=args.force, images_only=True)
    elif args.all:
        fetcher.process_all(genre=args.genre, force=args.force, images_only=True)
    
    # Legacy single-band mode
    elif args.artist:
        print(f"Searching for: {args.artist}")
        artist_data = fetcher.search_artist(args.artist)
        
        if not artist_data:
            print("✗ Artist not found in TheAudioDB", file=sys.stderr)
            sys.exit(1)
        
        artist_name = artist_data.get('strArtist', args.artist)
        print(f"✓ Found: {artist_name}")
        print()
        
        # Download images if requested
        if args.download_images:
            print(f"Downloading images to: {args.download_images}")
            downloaded, skipped = fetcher.download_all_images(artist_data, args.download_images)
            print(f"✓ Downloaded: {len(downloaded)}")
            if args.verbose and skipped:
                print(f"⊘ Skipped: {', '.join(skipped)}")
            print()
        
        # Output format
        if args.raw:
            print(json.dumps(artist_data, indent=2))
        elif args.json:
            formatted = fetcher.format_json(artist_data)
            output = json.dumps(formatted, indent=2)
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
                print(f"✓ Saved JSON to: {args.output}")
            else:
                print(output)
        else:
            markdown = fetcher.format_markdown(artist_data)
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(markdown)
                print(f"✓ Saved markdown to: {args.output}")
            else:
                print(markdown)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
