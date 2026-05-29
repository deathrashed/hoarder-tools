#!/usr/bin/env python3
"""
Fetch lyrics from Metal Archives (metallum-style)
Fetches lyrics from metal-archives.com and saves them as .lrc files
for use with lyrics_embed_from_lrc.py

Based on metallum: https://github.com/noeldelgado/metallum
"""

import os
import sys
import argparse
import subprocess
import re
from pathlib import Path
from urllib.parse import quote, urljoin
from rich.console import Console

console = Console()

class MetalArchivesLyricsFetcher:
    """Fetcher for lyrics from Metal Archives."""
    
    def __init__(self):
        self.session_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    def search_song(self, band_name, song_title):
        """Search for a song on Metal Archives."""
        try:
            from bs4 import BeautifulSoup
            
            # Build search URL
            search_url = f"https://www.metal-archives.com/search/ajax-advanced/searching/songs/?bandName={quote(band_name)}&songTitle={quote(song_title)}"
            
            # Use curl to fetch (works when Python requests are blocked)
            try:
                result = subprocess.run(
                    ['curl', '-s', '-H', f'User-Agent: {self.session_headers["User-Agent"]}', search_url],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    import json
                    data = json.loads(result.stdout)
                else:
                    raise Exception("curl failed")
            except Exception as e:
                # Fallback to urllib
                import urllib.request
                import json
                
                req = urllib.request.Request(search_url)
                req.add_header('User-Agent', self.session_headers['User-Agent'])
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode('utf-8'))
            
            aa_data = data.get('aaData', [])
            if not aa_data or len(aa_data) == 0:
                return None
            
            # Get first result
            first_result = aa_data[0]
            if not first_result or len(first_result) < 2:
                return None
            
            # Parse the HTML result to get song URL
            soup = BeautifulSoup(first_result[0], 'html.parser')
            link = soup.find('a')
            if not link:
                return None
            
            song_url = link.get('href', '')
            if not song_url.startswith('http'):
                song_url = urljoin('https://www.metal-archives.com', song_url)
            
            return song_url
            
        except Exception as e:
            console.print(f"[red]Error searching for song: {e}[/red]")
            return None
    
    def fetch_lyrics(self, song_url):
        """Fetch lyrics from a song URL."""
        try:
            from bs4 import BeautifulSoup
            
            # Fetch song page
            try:
                result = subprocess.run(
                    ['curl', '-s', '-H', f'User-Agent: {self.session_headers["User-Agent"]}', song_url],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    html = result.stdout
                else:
                    raise Exception("curl failed")
            except Exception as e:
                # Fallback to urllib
                import urllib.request
                
                req = urllib.request.Request(song_url)
                req.add_header('User-Agent', self.session_headers['User-Agent'])
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    html = response.read().decode('utf-8')
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find lyrics section
            # Metal Archives typically has lyrics in a div with class "lyrics" or similar
            lyrics_div = soup.find('div', class_=lambda x: x and 'lyrics' in str(x).lower())
            if not lyrics_div:
                # Try finding by id
                lyrics_div = soup.find('div', id=lambda x: x and 'lyrics' in str(x).lower())
            if not lyrics_div:
                # Try finding any div containing "Lyrics" text
                for div in soup.find_all('div'):
                    if div.get_text() and 'lyrics' in div.get_text().lower()[:100]:
                        lyrics_div = div
                        break
            
            if not lyrics_div:
                return None
            
            # Extract lyrics text
            lyrics_text = lyrics_div.get_text(separator='\n', strip=True)
            
            # Clean up lyrics
            # Remove "Lyrics:" header if present
            lyrics_text = re.sub(r'^lyrics:?\s*', '', lyrics_text, flags=re.IGNORECASE)
            lyrics_text = lyrics_text.strip()
            
            if not lyrics_text or len(lyrics_text) < 10:
                return None
            
            return lyrics_text
            
        except Exception as e:
            console.print(f"[red]Error fetching lyrics: {e}[/red]")
            return None
    
    def save_lyrics(self, lyrics_text, output_path):
        """Save lyrics to a file."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(lyrics_text)
            return True
        except Exception as e:
            console.print(f"[red]Error saving lyrics: {e}[/red]")
            return False
    
    def fetch_and_save(self, band_name, song_title, output_path=None, dry_run=False):
        """Fetch lyrics and save to file."""
        console.print(f"\n[bold cyan]Searching for:[/bold cyan] {band_name} - {song_title}")
        
        # Search for song
        song_url = self.search_song(band_name, song_title)
        if not song_url:
            console.print(f"[red]✗ Song not found: {band_name} - {song_title}[/red]")
            return False
        
        console.print(f"[green]✓ Found song URL:[/green] {song_url}")
        
        # Fetch lyrics
        lyrics = self.fetch_lyrics(song_url)
        if not lyrics:
            console.print(f"[red]✗ Lyrics not found for: {band_name} - {song_title}[/red]")
            return False
        
        if dry_run:
            console.print(f"[yellow]Would save lyrics to:[/yellow] {output_path}")
            console.print(f"[dim]{lyrics[:200]}...[/dim]")
            return True
        
        # Save lyrics
        if self.save_lyrics(lyrics, output_path):
            console.print(f"[green]✓ Lyrics saved to:[/green] {output_path}")
            return True
        else:
            return False


def find_audio_files(directory):
    """Find all audio files in a directory."""
    audio_exts = ['.flac', '.mp3', '.m4a', '.ogg', '.wav', '.aac']
    audio_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in audio_exts):
                audio_files.append(Path(root) / file)
    
    return audio_files


def extract_metadata(audio_path):
    """Extract artist and title from audio file."""
    try:
        from mutagen.flac import FLAC
        from mutagen.id3 import ID3, EasyID3
        from mutagen.mp3 import MP3
        
        if audio_path.suffix.lower() == '.flac':
            audio = FLAC(audio_path)
            artist = audio.get('artist', ['Unknown'])[0]
            title = audio.get('title', ['Unknown'])[0]
        elif audio_path.suffix.lower() == '.mp3':
            try:
                easy = EasyID3(audio_path)
                artist = easy.get('artist', ['Unknown'])[0]
                title = easy.get('title', ['Unknown'])[0]
            except:
                audio = MP3(audio_path, ID3=ID3)
                artist = 'Unknown'
                title = 'Unknown'
        else:
            return None, None
        
        return artist, title
    except Exception as e:
        return None, None


def process_directory(directory, dry_run=False, verbose=False):
    """Process all audio files in a directory and fetch lyrics."""
    directory = Path(directory)
    if not directory.exists():
        console.print(f"[red]Error: Directory does not exist: {directory}[/red]")
        return
    
    audio_files = find_audio_files(directory)
    if not audio_files:
        console.print(f"[yellow]No audio files found in: {directory}[/yellow]")
        return
    
    console.print(f"\n[bold cyan]Found {len(audio_files)} audio files[/bold cyan]")
    
    fetcher = MetalArchivesLyricsFetcher()
    fetched = 0
    skipped = 0
    failed = 0
    
    for audio_file in audio_files:
        # Extract metadata
        artist, title = extract_metadata(audio_file)
        if not artist or not title or artist == 'Unknown' or title == 'Unknown':
            if verbose:
                console.print(f"[yellow]Skipping {audio_file.name}: missing metadata[/yellow]")
            skipped += 1
            continue
        
        # Check if .lrc already exists
        lrc_path = audio_file.with_suffix('.lrc')
        if lrc_path.exists():
            if verbose:
                console.print(f"[cyan]Skipping {audio_file.name}: .lrc already exists[/cyan]")
            skipped += 1
            continue
        
        # Fetch lyrics
        if fetcher.fetch_and_save(artist, title, lrc_path, dry_run):
            fetched += 1
        else:
            failed += 1
    
    console.print(f"\n[bold underline]Summary[/bold underline]")
    console.print(f"Lyrics fetched: {fetched}")
    console.print(f"Skipped: {skipped}")
    console.print(f"Failed: {failed}")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")


def main():
    parser = argparse.ArgumentParser(
        description='Fetch lyrics from Metal Archives (metallum-style)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch lyrics for a specific song
  python lyrics_fetch_metal_archives.py "Iron Maiden" "The Trooper"
  
  # Process all audio files in a directory
  python lyrics_fetch_metal_archives.py -d /path/to/music --dry-run
  python lyrics_fetch_metal_archives.py -d /path/to/music --verbose
  
  # Fetch and save to specific file
  python lyrics_fetch_metal_archives.py "Therion" "Quetzalcoatl" -o /path/to/quetzalcoatl.lrc
        """
    )
    
    parser.add_argument(
        'band_name',
        nargs='?',
        help='Band name (required if not using -d)'
    )
    parser.add_argument(
        'song_title',
        nargs='?',
        help='Song title (required if not using -d)'
    )
    parser.add_argument(
        '-d', '--directory',
        help='Process all audio files in directory'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file path (for single song fetch)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview actions without saving files'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed output'
    )
    
    args = parser.parse_args()
    
    fetcher = MetalArchivesLyricsFetcher()
    
    if args.directory:
        # Process directory
        process_directory(args.directory, args.dry_run, args.verbose)
    elif args.band_name and args.song_title:
        # Fetch single song
        if args.output:
            output_path = Path(args.output)
        else:
            # Default: save as song_title.lrc in current directory
            safe_title = re.sub(r'[^\w\s-]', '', args.song_title).strip()
            output_path = Path(f"{safe_title}.lrc")
        
        fetcher.fetch_and_save(args.band_name, args.song_title, output_path, args.dry_run)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

