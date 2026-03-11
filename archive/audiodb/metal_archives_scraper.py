#!/usr/bin/env python3
"""
Metal Archives Band Image Scraper
Scrapes full-sized logos and band photos from Metal Archives
and saves them to band folders.

Uses direct Metal Archives API access.
"""

import os
import sys
import argparse
from pathlib import Path
import requests
from PIL import Image
import io

# Note: We use direct Metal Archives API access (same approach as Script Kit scripts)
# This works better than enmet for avoiding blocking issues


class MetalArchivesImageScraper:
    """Scraper for Metal Archives band logos and photos."""
    
    def __init__(self, base_path="/Volumes/Eksternal/Audio"):
        self.base_path = Path(base_path)
        self.session = requests.Session()
        # Use minimal headers that work (like curl)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        })
    
    def get_albums_from_folder(self, band_folder):
        """Extract album/release names from band folder."""
        albums = []
        try:
            if not band_folder.exists():
                return albums
            
            # Look for common album folder patterns
            for item in band_folder.iterdir():
                if item.is_dir():
                    # Album folder name
                    album_name = item.name
                    # Clean up common patterns
                    album_name = album_name.split(' - ')[-1]  # Remove "Year - Album" format
                    album_name = album_name.split(' (')[0]  # Remove "(Year)" or "(Type)"
                    album_name = album_name.strip()
                    if album_name:
                        albums.append(album_name.lower())
            
            return albums
        except Exception as e:
            return albums
    
    def get_band_discography(self, band_url):
        """Get band's discography from Metal Archives."""
        try:
            import subprocess
            from bs4 import BeautifulSoup
            
            # Fetch band page using curl
            result = subprocess.run(
                ['curl', '-s', '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', band_url],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return []
            
            soup = BeautifulSoup(result.stdout, 'html.parser')
            albums = []
            
            # Find discography section - Metal Archives has albums in a table
            # Look for album links in the discography table
            discography_table = soup.find('table', {'id': 'discography'}) or soup.find('table', class_=lambda x: x and 'discography' in str(x).lower())
            
            if discography_table:
                for link in discography_table.find_all('a', href=lambda x: x and '/albums/' in x):
                    album_name = link.get_text(strip=True)
                    if album_name:
                        # Clean up album name
                        album_name = album_name.split(' (')[0]  # Remove "(Year)" or "(Type)"
                        album_name = album_name.strip()
                        albums.append(album_name.lower())
            else:
                # Fallback: look for any album links on the page
                for link in soup.find_all('a', href=lambda x: x and '/albums/' in x):
                    album_name = link.get_text(strip=True)
                    if album_name and len(album_name) > 2:  # Filter out very short names
                        album_name = album_name.split(' (')[0]
                        album_name = album_name.strip()
                        if album_name not in albums:
                            albums.append(album_name.lower())
            
            return albums
        except Exception as e:
            return []
    
    def match_band_by_albums(self, candidates, folder_albums):
        """Match band candidates by comparing their discography with folder albums."""
        if not folder_albums:
            return None
        
        best_match = None
        best_score = 0
        
        for candidate in candidates:
            band_url = candidate['url']
            band_name = candidate['name']
            
            # Get discography for this band
            discography = self.get_band_discography(band_url)
            
            if not discography:
                continue
            
            # Calculate match score
            matches = 0
            for folder_album in folder_albums:
                # Check for exact match
                if folder_album in discography:
                    matches += 2
                else:
                    # Check for partial match (substring)
                    for disc_album in discography:
                        if folder_album in disc_album or disc_album in folder_album:
                            matches += 1
                            break
            
            # Score is matches / total folder albums
            if folder_albums:
                score = matches / len(folder_albums)
            else:
                score = 0
            
            if score > best_score:
                best_score = score
                best_match = candidate
        
        # Only return if we have a reasonable match (at least 30% match)
        if best_score >= 0.3:
            return best_match
        
        return None
    
    def get_band_info(self, band_name, band_folder=None):
        """Get band information from Metal Archives using direct API access."""
        try:
            import time
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin
            
            # Get albums from folder if provided
            folder_albums = []
            if band_folder:
                folder_albums = self.get_albums_from_folder(band_folder)
                if folder_albums:
                    print(f"Found {len(folder_albums)} albums in folder to match against")
            
            # Use Metal Archives search API (same endpoint as Script Kit scripts use)
            # Build URL with query params directly (like curl does)
            from urllib.parse import quote
            search_url = f"https://www.metal-archives.com/search/ajax-band-search/?field=name&query={quote(band_name)}"
            
            # Try using curl via subprocess first (works reliably), then fallback to urllib/requests
            import subprocess
            import json
            
            try:
                # Use curl directly (works when Python requests are blocked)
                result = subprocess.run(
                    ['curl', '-s', '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', search_url],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                else:
                    raise Exception("curl failed")
            except Exception as e:
                # Fallback to urllib
                try:
                    import urllib.request
                    
                    req = urllib.request.Request(search_url)
                    req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
                    
                    with urllib.request.urlopen(req, timeout=10) as response:
                        data = json.loads(response.read().decode('utf-8'))
                except Exception as e2:
                    # Final fallback to requests
                    response = self.session.get(search_url, timeout=10)
                    
                    if response.status_code != 200:
                        print(f"Error: HTTP {response.status_code} from Metal Archives")
                        return None
                    
                    try:
                        data = response.json()
                    except:
                        print(f"Error: Metal Archives returned invalid JSON response")
                        print(f"This may indicate blocking or server issues")
                        return None
            
            aa_data = data.get('aaData', [])
            if not aa_data or len(aa_data) == 0:
                print(f"No bands found matching '{band_name}'")
                return None
            
            # Extract all band candidates
            candidates = []
            exact_matches = []
            
            for row in aa_data:
                first_col = row[0] if row else ''
                if not first_col:
                    continue
                
                soup = BeautifulSoup(first_col, 'html.parser')
                link = soup.find('a')
                if link:
                    found_name = link.get_text(strip=True)
                    url = link.get('href', '')
                    
                    if not url.startswith('http'):
                        url = urljoin('https://www.metal-archives.com', url)
                    
                    candidate = {'name': found_name, 'url': url}
                    candidates.append(candidate)
                    
                    # Check for exact match (case-insensitive)
                    if found_name.lower() == band_name.lower():
                        exact_matches.append(candidate)
            
            if not candidates:
                print(f"No bands found matching '{band_name}'")
                return None
            
            # If we have folder albums, try to match by discography
            if folder_albums and len(candidates) > 1:
                print(f"Matching against discography for {len(candidates)} candidates...")
                matched_band = self.match_band_by_albums(candidates, folder_albums)
                if matched_band:
                    print(f"Matched by discography: {matched_band['name']}")
                    band_url = matched_band['url']
                    band_name_found = matched_band['name']
                elif exact_matches:
                    # Use exact match if available
                    band_url = exact_matches[0]['url']
                    band_name_found = exact_matches[0]['name']
                    print(f"Using exact name match: {band_name_found}")
                else:
                    # Use first result
                    band_url = candidates[0]['url']
                    band_name_found = candidates[0]['name']
                    print(f"Warning: Multiple bands found, using first result: {band_name_found}")
            elif exact_matches:
                # Use exact match if available
                band_url = exact_matches[0]['url']
                band_name_found = exact_matches[0]['name']
            else:
                # Use first result
                band_url = candidates[0]['url']
                band_name_found = candidates[0]['name']
                if len(candidates) > 1:
                    print(f"Warning: Multiple bands found, using first result: {band_name_found}")
            
            # Create a simple object with url attribute
            class BandInfo:
                def __init__(self, url, name):
                    self.url = url
                    self.name = name
                    self.id = None
            
            return BandInfo(band_url, band_name_found)
                
        except Exception as e:
            error_msg = str(e)
            if "JSONDecodeError" in error_msg or "Expecting value" in error_msg:
                print(f"Error: Metal Archives may be blocking requests or returning empty responses.")
                print(f"This could be due to:")
                print(f"  1. Temporary rate limiting - wait a few minutes and try again")
                print(f"  2. IP blocking - try using a VPN or different network")
                print(f"  3. Metal Archives server issues - try again later")
            else:
                print(f"Error searching for band '{band_name}': {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_image_urls(self, band):
        """Extract logo and photo URLs from band object."""
        images = {}
        
        try:
            from urllib.parse import urljoin
            from bs4 import BeautifulSoup
            import re
            
            # Get band page URL
            band_url = getattr(band, 'url', None)
            if not band_url:
                print("Could not determine band URL")
                return images
            
            # Fetch the band page HTML using curl (works when Python requests are blocked)
            import subprocess
            
            try:
                result = subprocess.run(
                    ['curl', '-s', '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', band_url],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    band_html = result.stdout
                else:
                    raise Exception("curl failed")
            except Exception as e:
                # Fallback to requests
                response = self.session.get(band_url, timeout=10)
                response.raise_for_status()
                band_html = response.text
            
            # Use multiple regex patterns to find logo URL (same approach as Script Kit scripts)
            patterns = [
                r'<a[^>]+id=["\']logo["\'][^>]+href=["\']([^"\']+)["\']',
                r'<img[^>]+id=["\']logo["\'][^>]+src=["\']([^"\']+)["\']',
                r'<img[^>]+class=["\'][^"\']*logo[^"\']*["\'][^>]+src=["\']([^"\']+)["\']',
                r'<a[^>]+href=["\'](https?://[^"\']+/images/[^"\']+logo[^"\']+\.(?:png|jpg|jpeg|gif))["\'][^>]*>',
            ]
            
            logo_url = None
            for pattern in patterns:
                match = re.search(pattern, band_html, re.IGNORECASE)
                if match and match.group(1):
                    logo_url = match.group(1)
                    break
            
            # Also try BeautifulSoup as fallback
            soup = None
            if not logo_url:
                soup = BeautifulSoup(band_html, 'html.parser')
                
                # Find logo - try multiple methods
                logo_elem = soup.find('a', {'id': 'logo'})
                if logo_elem:
                    logo_url = logo_elem.get('href', '')
                else:
                    logo_elem = soup.find('img', {'id': 'logo'})
                    if logo_elem:
                        logo_url = logo_elem.get('src', '')
                    else:
                        # Try finding by class
                        logo_elem = soup.find('img', class_=lambda x: x and 'logo' in x.lower())
                        if logo_elem:
                            logo_url = logo_elem.get('src', '')
                        else:
                            # Last resort: search all images for logo-like URLs
                            for img in soup.find_all('img'):
                                src = img.get('src', '')
                                if src and ('logo' in src.lower() or 'band_logo' in src.lower()):
                                    logo_url = src
                                    break
            
            if logo_url:
                # Convert to full-size (remove thumb/small suffixes)
                logo_url = logo_url.replace('_thumb', '').replace('_small', '').replace('_medium', '')
                # Make URL absolute if needed
                if not logo_url.startswith('http'):
                    logo_url = urljoin(band_url, logo_url)
                images['logo'] = logo_url
            
            # Find band photo using similar approach
            photo_patterns = [
                r'<a[^>]+id=["\']photo["\'][^>]+href=["\']([^"\']+)["\']',
                r'<img[^>]+id=["\']photo["\'][^>]+src=["\']([^"\']+)["\']',
                r'<img[^>]+class=["\'][^"\']*photo[^"\']*["\'][^>]+src=["\']([^"\']+)["\']',
            ]
            
            photo_url = None
            for pattern in photo_patterns:
                match = re.search(pattern, band_html, re.IGNORECASE)
                if match and match.group(1):
                    photo_url = match.group(1)
                    break
            
            # Also try BeautifulSoup as fallback
            if not photo_url:
                if soup is None:
                    soup = BeautifulSoup(band_html, 'html.parser')
                
                photo_elem = soup.find('a', {'id': 'photo'})
                if photo_elem:
                    photo_url = photo_elem.get('href', '')
                else:
                    photo_elem = soup.find('img', {'id': 'photo'})
                    if photo_elem:
                        photo_url = photo_elem.get('src', '')
                    else:
                        # Try finding by class
                        photo_elem = soup.find('img', class_=lambda x: x and 'photo' in x.lower())
                        if photo_elem:
                            photo_url = photo_elem.get('src', '')
                        else:
                            # Last resort: search all images for photo-like URLs
                            for img in soup.find_all('img'):
                                src = img.get('src', '')
                                if src and ('photo' in src.lower() or 'band_photo' in src.lower()):
                                    photo_url = src
                                    break
            
            if photo_url:
                # Convert to full-size (remove thumb/small suffixes)
                photo_url = photo_url.replace('_thumb', '').replace('_small', '').replace('_medium', '')
                # Make URL absolute if needed
                if not photo_url.startswith('http'):
                    photo_url = urljoin(band_url, photo_url)
                images['photo'] = photo_url
            
        except Exception as e:
            print(f"Error extracting image URLs: {e}")
            import traceback
            traceback.print_exc()
        
        return images
    
    def download_image(self, url, output_path):
        """Download an image from URL to output path."""
        try:
            import subprocess
            
            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Try using curl first (works when Python requests are blocked)
            try:
                result = subprocess.run(
                    ['curl', '-s', '-L', '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', '-o', str(output_path), url],
                    timeout=30
                )
                
                if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
                    return True
                else:
                    raise Exception("curl download failed")
            except Exception as e:
                # Fallback to requests
                response = self.session.get(url, timeout=30, stream=True)
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('content-type', '')
                if 'image' not in content_type:
                    print(f"Warning: {url} may not be an image (content-type: {content_type})")
                
                # Download image
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                return True
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False
    
    def process_band(self, band_folder_path):
        """Process a single band folder."""
        band_folder = Path(band_folder_path)
        
        if not band_folder.exists():
            print(f"Error: Band folder does not exist: {band_folder}")
            return False
        
        # Extract band name from folder path
        band_name = band_folder.name
        
        print(f"\n{'='*60}")
        print(f"Processing: {band_name}")
        print(f"Folder: {band_folder}")
        print(f"{'='*60}")
        
        # Check if images already exist
        logo_path = band_folder / 'logo.png'
        photo_path = band_folder / 'artist.jpg'
        
        # Check if force flag is set (will be passed via instance variable)
        force = getattr(self, 'force', False)
        
        if not force and logo_path.exists() and photo_path.exists():
            print(f"Images already exist for {band_name}. Skipping...")
            print("Use --force to re-download.")
            return True
        
        # Get band information (pass band folder to match by albums)
        band = self.get_band_info(band_name, band_folder)
        if not band:
            return False
        
        band_name_found = getattr(band, 'name', band_name)
        band_id = getattr(band, 'id', None)
        band_url = None
        
        # Try to get URL from band object
        if hasattr(band, 'url'):
            band_url = band.url
        elif band_id:
            band_url = f"https://www.metal-archives.com/bands/{band_id}"
        
        print(f"Found band: {band_name_found}")
        if band_id:
            print(f"Band ID: {band_id}")
        if band_url:
            print(f"Band URL: {band_url}")
        
        # Get image URLs
        images = self.get_image_urls(band)
        
        if not images:
            print(f"No images found for {band_name}")
            return False
        
        success = True
        
        # Download logo (no background removal)
        if images.get('logo'):
            print(f"\nDownloading logo from: {images['logo']}")
            if self.download_image(images['logo'], logo_path):
                print(f"✓ Logo saved successfully: {logo_path}")
            else:
                print("✗ Failed to download logo")
                success = False
        else:
            print("No logo found")
        
        # Download band photo
        if images.get('photo'):
            print(f"\nDownloading photo from: {images['photo']}")
            if self.download_image(images['photo'], photo_path):
                print(f"✓ Photo saved successfully: {photo_path}")
            else:
                print("✗ Failed to download photo")
                success = False
        else:
            print("No band photo found")
        
        return success
    
    def process_all_bands(self, genre_path=None):
        """Process all bands in the directory structure."""
        if genre_path is None:
            genre_path = self.base_path / "Metal"
        else:
            genre_path = Path(genre_path)
        
        if not genre_path.exists():
            print(f"Error: Genre path does not exist: {genre_path}")
            return
        
        print(f"Scanning for band folders in: {genre_path}")
        
        # Find all potential band folders
        # A band folder is one that contains album subdirectories (not music files directly)
        band_folders = []
        seen_band_folders = set()
        
        # First pass: identify band folders (those with album subdirectories)
        for root, dirs, files in os.walk(genre_path):
            root_path = Path(root)
            
            # Skip if this is the base genre path
            if root_path == genre_path:
                continue
            
            # Check if this folder has music files directly (likely an album folder, not band folder)
            has_music_files = any(f.lower().endswith(('.mp3', '.flac', '.m4a', '.wav', '.ogg', '.aac')) 
                                 for f in files)
            
            # Check if it has subdirectories (likely album folders)
            has_subdirs = bool(dirs)
            
            # A band folder is one that:
            # 1. Has subdirectories (album folders), OR
            # 2. Has music files AND is at a certain depth (likely a band folder with albums as subdirs)
            # 3. Is NOT a leaf node with music files (those are album folders)
            
            # Calculate depth from genre_path
            try:
                depth = len(root_path.relative_to(genre_path).parts)
            except:
                depth = 0
            
            # Band folders are typically at depth 1 (e.g., Metal/D/BandName/)
            # Album folders are typically at depth 2+ (e.g., Metal/D/BandName/AlbumName/)
            is_band_folder = False
            
            if has_subdirs and not has_music_files:
                # Has subdirectories but no music files directly = band folder
                is_band_folder = True
            elif has_subdirs and has_music_files and depth <= 1:
                # Has both but at shallow depth = likely band folder
                is_band_folder = True
            elif not has_subdirs and not has_music_files:
                # Empty folder, skip
                continue
            elif not has_subdirs and has_music_files and depth <= 1:
                # Leaf node with music at shallow depth = might be a band folder
                # (some bands have music directly in their folder)
                is_band_folder = True
            
            if is_band_folder:
                # Check if it doesn't already have both images
                logo_path = root_path / 'logo.png'
                photo_path = root_path / 'artist.jpg'
                
                if not (logo_path.exists() and photo_path.exists()):
                    # Avoid duplicates
                    if root_path not in seen_band_folders:
                        band_folders.append(root_path)
                        seen_band_folders.add(root_path)
        
        print(f"\nFound {len(band_folders)} band folders to process")
        
        if not band_folders:
            print("No band folders found or all already have images.")
            return
        
        # Process each band
        successful = 0
        failed = 0
        
        for i, folder in enumerate(band_folders, 1):
            print(f"\n[{i}/{len(band_folders)}]")
            if self.process_band(folder):
                successful += 1
            else:
                failed += 1
        
        print(f"\n{'='*60}")
        print(f"Processing complete!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description='Scrape Metal Archives for band logos and photos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a specific band
  python metal_archives_scraper.py /Volumes/Eksternal/Audio/Metal/D/Diabolic
  
  # Process all bands in Metal directory
  python metal_archives_scraper.py --all
  
  # Use a different base path
  python metal_archives_scraper.py --base-path /Volumes/Eksternal/Audio --all
        """
    )
    
    parser.add_argument(
        'band_path',
        nargs='?',
        help='Path to specific band folder (e.g., /Volumes/Eksternal/Audio/Metal/D/Diabolic)'
    )
    parser.add_argument(
        '--base-path',
        default='/Volumes/Eksternal/Audio',
        help='Base path for audio directory (default: /Volumes/Eksternal/Audio)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all bands in the Metal directory (or specified path)'
    )
    parser.add_argument(
        '--path',
        help='Specific path to process (can be used with --all to process a subdirectory)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Re-download images even if they already exist'
    )
    
    args = parser.parse_args()
    
    # Script uses direct Metal Archives API access (no external library required)
    
    scraper = MetalArchivesImageScraper(args.base_path)
    scraper.force = args.force
    
    if args.all or not args.band_path:
        # If --path is specified, use it; otherwise use default Metal directory
        if args.path:
            scraper.process_all_bands(args.path)
        else:
            scraper.process_all_bands()
    else:
        scraper.process_band(args.band_path)


if __name__ == '__main__':
    main()

