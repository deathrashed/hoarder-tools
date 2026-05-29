#!/usr/bin/env python3
"""
MP3 Genres from Discogs (Style Field)
=====================================
Fetches the "style" field from Discogs and appends it to the Genre tag.

Discogs uses:
- "genre" for broad categories (e.g., "Rock")
- "style" for specific subgenres (e.g., "Crossover Thrash, Hardcore")

This script appends the style values to the existing genre field, separated by semicolons.

Usage:
    1) Get a Discogs user token: https://www.discogs.com/settings/developers
    2) Set environment variable: export DISCOGS_USER_TOKEN=your_token
       Or create ~/.env file with: DISCOGS_USER_TOKEN=your_token
    3) Run: python3 metadata_fetch_genres_discogs.py /path/to/mp3/folder
       Or: python3 metadata_fetch_genres_discogs.py  (will prompt for folder)

The script will:
    - Read each MP3's "artist" and "album" tags
    - Search Discogs for the release
    - Extract the "style" field (specific genres)
    - Append styles to existing Genre field, separated by semicolons
    - If Genre is empty, sets it to the styles

Notes:
    - Handles API rate limiting with delays
    - Only files with both "artist" and "album" tags will be processed
    - Example: Genre="Rock" + Style="Crossover Thrash, Hardcore" 
               → Genre="Rock; Crossover Thrash; Hardcore"
"""

import os
import sys
import re
import time
from pathlib import Path
from urllib.parse import quote

# Try to load environment variables from .env file
try:
    env_path = Path.home() / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and not os.environ.get(key):
                        os.environ[key] = value
except Exception:
    pass

# Get Discogs token
DISCOGS_USER_TOKEN = os.environ.get('DISCOGS_USER_TOKEN')

if not DISCOGS_USER_TOKEN:
    print('Error: DISCOGS_USER_TOKEN environment variable is not set.', file=sys.stderr)
    print('Get a Discogs user token: https://www.discogs.com/settings/developers', file=sys.stderr)
    print('Then set: export DISCOGS_USER_TOKEN=your_token', file=sys.stderr)
    print('Or add DISCOGS_USER_TOKEN=your_token to ~/.env', file=sys.stderr)
    sys.exit(1)

# Try to import required libraries
try:
    from mutagen.id3 import ID3, ID3NoHeaderError, TCON, TPE1, TALB
    from mutagen.mp3 import MP3
except ImportError:
    print('Error: mutagen package not found.', file=sys.stderr)
    print('Install: pip3 install mutagen', file=sys.stderr)
    sys.exit(1)

try:
    import discogs_client
except ImportError:
    print('Error: discogs-client package not found.', file=sys.stderr)
    print('Install: pip3 install discogs-client', file=sys.stderr)
    sys.exit(1)

# Initialize Discogs client
try:
    d = discogs_client.Client('MP3GenreFetcher/1.0', user_token=DISCOGS_USER_TOKEN)
except Exception as e:
    print(f'Error initializing Discogs client: {e}', file=sys.stderr)
    sys.exit(1)


def find_mp3_files(directory):
    """Recursively find all MP3 files in directory."""
    mp3_files = []
    directory = Path(directory)
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.mp3'):
                mp3_files.append(Path(root) / file)
    
    return mp3_files


def get_mp3_tags(file_path):
    """Extract artist and album from MP3 tags."""
    try:
        audio = MP3(str(file_path), ID3=ID3)
        
        # Get artist (TPE1)
        artist = None
        if 'TPE1' in audio:
            artist = str(audio['TPE1'][0]).strip()
        
        # Get album (TALB)
        album = None
        if 'TALB' in audio:
            album = str(audio['TALB'][0]).strip()
        
        # Get current genre (TCON)
        current_genre = None
        if 'TCON' in audio:
            current_genre = str(audio['TCON'][0]).strip()
        
        return {
            'artist': artist,
            'album': album,
            'genre': current_genre,
            'audio': audio
        }
    except ID3NoHeaderError:
        return None
    except Exception as e:
        print(f"  Error reading {file_path.name}: {e}", file=sys.stderr)
        return None


def search_discogs_release(artist, album):
    """Search Discogs for a release by artist and album."""
    try:
        # Search for releases
        query = f"{artist} {album}"
        results = d.search(query, type='release')
        
        # Rate limiting
        time.sleep(0.5)
        
        # When searching with type='release', results are already Release objects
        # Try to find best match
        for result in results:
            try:
                # Get full release details
                release = d.release(result.id)
                time.sleep(0.5)  # Rate limiting
                
                # Check if artist and album match reasonably
                release_artist = release.artists[0].name if release.artists else ""
                release_title = release.title
                
                # Simple matching (case-insensitive)
                artist_match = artist.lower() in release_artist.lower() or release_artist.lower() in artist.lower()
                album_match = album.lower() in release_title.lower() or release_title.lower() in album.lower()
                
                if artist_match and album_match:
                    return release
            except Exception:
                continue
        
        # If no exact match, return first result
        for result in results:
            try:
                release = d.release(result.id)
                time.sleep(0.5)
                return release
            except Exception:
                continue
        
        return None
        
    except Exception as e:
        if 'rate limit' in str(e).lower() or '429' in str(e):
            time.sleep(2)
            return None
        # Silently return None on other errors
        return None


def get_styles_from_release(release):
    """Extract style values from Discogs release."""
    if not release:
        return []
    
    styles = []
    try:
        # Get styles (this is a list)
        if hasattr(release, 'styles') and release.styles:
            styles = [str(s).strip() for s in release.styles if s]
    except Exception:
        pass
    
    return styles


def to_mixed_case(text):
    """Capitalize words properly (like Last.fm script)."""
    if not text:
        return ""
    lower = text.lower().strip()
    # Capitalize first letter of each word
    cased = re.sub(
        r'\b([a-z])([a-z0-9\'&]*)\b',
        lambda m: m.group(1).upper() + m.group(2),
        lower
    )
    return re.sub(r'\s+', ' ', cased).strip()


def normalize_style(style):
    """Normalize style name using Last.fm-style expansion logic."""
    if not style:
        return ""
    
    style_lower = style.lower().strip()
    
    # Slash expansions (from Last.fm script)
    slash_expansions = {
        "death/thrash": ["Death/Thrash", "Death Metal", "Thrash Metal"],
        "thrash/death": ["Thrash/Death", "Thrash Metal", "Death Metal"],
        "death/doom": ["Death/Doom", "Death Metal", "Doom Metal"],
        "doom/death": ["Doom/Death", "Doom Metal", "Death Metal"],
        "black/death": ["Black/Death", "Black Metal", "Death Metal"],
        "death/black": ["Death/Black", "Death Metal", "Black Metal"],
        "black/thrash": ["Black/Thrash", "Black Metal", "Thrash Metal"],
        "thrash/black": ["Thrash/Black", "Thrash Metal", "Black Metal"],
    }
    
    # Genre expansions (from Last.fm script, but Punk stays as Punk)
    genre_expansions = {
        'thrash': 'Thrash Metal',
        'death': 'Death Metal',
        'black': 'Black Metal',
        'doom': 'Doom Metal',
        'heavy': 'Heavy Metal',
        'hardcore': 'Hardcore',
        'punk': 'Punk',  # Keep as Punk (not Punk Rock) for Pop Punk, Hardcore Punk, etc.
        'folk': 'Folk Metal',
        'progressive': 'Progressive Metal',
        'power': 'Power Metal',
        'symphonic': 'Symphonic Metal',
        'sludge': 'Sludge Metal',
        'stoner': 'Stoner Rock',
        'speed': 'Speed Metal',
        'gothic': 'Gothic Metal',
        'groove': 'Groove Metal',
        'funk': 'Funk Metal',
        'alternative': 'Alternative Rock',
        'indie': 'Indie Rock',
        'industrial': 'Industrial',
        'math': 'Mathcore',
        'horror': 'Horror Punk',
    }
    
    # Compound expansions (from Last.fm script)
    # These are split into separate genres (semicolon-separated)
    compound_expansions_split = {
        "crossover thrash": ["Crossover", "Thrash Metal"],
        "thrash crossover": ["Thrash Metal", "Crossover"],
        "beatdown hardcore": ["Beatdown", "Hardcore"],
        "hardcore beatdown": ["Hardcore", "Beatdown"],
    }
    
    # These stay as single compound genres
    compound_expansions_keep = {
        "sludge metal": ["Sludge Metal"],
        "stoner metal": ["Stoner Metal"],
        "stoner rock": ["Stoner Rock"],
        "death metal": ["Death Metal"],
        "thrash metal": ["Thrash Metal"],
        "black metal": ["Black Metal"],
        "doom metal": ["Doom Metal"],
        "heavy metal": ["Heavy Metal"],
        "hard rock": ["Hard Rock"],
        "classic rock": ["Classic Rock"],
        "punk rock": ["Punk Rock"],
        "alternative rock": ["Alternative Rock"],
        "progressive metal": ["Progressive Metal"],
        "power metal": ["Power Metal"],
        "folk metal": ["Folk Metal"],
        "symphonic metal": ["Symphonic Metal"],
        "gothic metal": ["Gothic Metal"],
        "groove metal": ["Groove Metal"],
        "speed metal": ["Speed Metal"],
        "funk metal": ["Funk Metal"],
        "indie rock": ["Indie Rock"],
        "hardcore punk": ["Hardcore Punk"],
        "pop punk": ["Pop Punk"],  # Keep as compound
        "hardcore punk": ["Hardcore Punk"],  # Keep as compound
    }
    
    # Combined lookup
    compound_expansions = {**compound_expansions_split, **compound_expansions_keep}
    
    # Check slash expansions first
    if style_lower in slash_expansions:
        # Return as semicolon-separated string
        return '; '.join(slash_expansions[style_lower])
    
    # Check compound expansions
    if style_lower in compound_expansions:
        if style_lower in compound_expansions_split:
            # Split into separate genres
            return '; '.join(compound_expansions[style_lower])
        else:
            # Keep as single compound genre
            return compound_expansions[style_lower][0]
    
    # Handle slash-separated genres (e.g., "death/thrash")
    slash_match = re.match(r'^(.+?)/(.+)$', style_lower)
    if slash_match:
        part1 = slash_match.group(1).strip()
        part2 = slash_match.group(2).strip()
        combined = to_mixed_case(f"{part1}/{part2}")
        expanded1 = normalize_style(part1)
        expanded2 = normalize_style(part2)
        # Combine all parts
        all_parts = [combined]
        if ';' in expanded1:
            all_parts.extend(expanded1.split('; '))
        else:
            all_parts.append(expanded1)
        if ';' in expanded2:
            all_parts.extend(expanded2.split('; '))
        else:
            all_parts.append(expanded2)
        # Remove duplicates and return
        seen = set()
        unique = []
        for p in all_parts:
            if p.lower() not in seen:
                unique.append(p)
                seen.add(p.lower())
        return '; '.join(unique)
    
    # Handle two-word compounds (e.g., "Crossover Thrash")
    words = re.split(r'[\s/&-]+', style)
    if len(words) >= 2:
        common_genres = {
            "metal", "rock", "punk", "hardcore", "core", "thrash", "death", "black",
            "doom", "folk", "progressive", "power", "symphonic", "alternative", "classic",
            "heavy", "beatdown", "crossover", "sludge", "stoner", "speed", "gothic",
            "groove", "funk", "indie", "industrial", "math", "horror", "grindcore",
            "deathcore", "mathcore",
        }
        
        last_word = words[-1].lower()
        if last_word in common_genres and len(words) == 2:
            first_part = to_mixed_case(words[0])
            expanded_second = genre_expansions.get(last_word) or to_mixed_case(last_word)
            return f"{first_part}; {expanded_second}"
    
    # Single word expansion
    if style_lower in genre_expansions:
        return genre_expansions[style_lower]
    
    # If it already contains "metal", just capitalize properly
    if 'metal' in style_lower:
        return to_mixed_case(style)
    
    # Default: capitalize properly
    return to_mixed_case(style)


def combine_genres(existing_genre, styles):
    """Replace existing genre with Discogs styles, separated by semicolons."""
    # Normalize styles - some may return semicolon-separated (e.g., "Crossover; Thrash Metal")
    all_normalized = []
    for s in styles:
        if s:
            normalized = normalize_style(s)
            # Split by semicolon if normalization created multiple genres
            if ';' in normalized:
                all_normalized.extend([ns.strip() for ns in normalized.split(';')])
            else:
                all_normalized.append(normalized)
    
    if not all_normalized:
        # If no styles found, keep existing genre
        return existing_genre if existing_genre else ""
    
    # Remove duplicates (case-insensitive)
    unique_styles = []
    seen = set()
    for style in all_normalized:
        style_lower = style.lower().strip()
        if style_lower and style_lower not in seen:
            unique_styles.append(style.strip())
            seen.add(style_lower)
    
    # Replace genre with Discogs styles (semicolon-separated)
    return '; '.join(unique_styles)


def update_mp3_genre(file_path, audio, new_genre):
    """Update the genre tag in MP3 file."""
    try:
        if 'TCON' in audio:
            audio['TCON'] = TCON(encoding=3, text=new_genre)
        else:
            audio.add(TCON(encoding=3, text=new_genre))
        
        audio.save()
        return True
    except Exception as e:
        print(f"  Error updating {file_path.name}: {e}", file=sys.stderr)
        return False


def main():
    # Get folder from command line or prompt
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = input('Enter folder path containing MP3 files: ').strip()
    
    if not folder:
        print('Error: No folder specified', file=sys.stderr)
        sys.exit(1)
    
    folder = Path(folder).resolve()
    
    if not folder.exists():
        print(f'Error: Folder does not exist: {folder}', file=sys.stderr)
        sys.exit(1)
    
    if not folder.is_dir():
        print(f'Error: Path is not a directory: {folder}', file=sys.stderr)
        sys.exit(1)
    
    print(f'\nSearching for MP3 files in: {folder}\n')
    
    # Find all MP3 files
    mp3_files = find_mp3_files(folder)
    
    if not mp3_files:
        print(f'No MP3 files found in: {folder}')
        sys.exit(0)
    
    print(f'Found {len(mp3_files)} MP3 file(s)\n')
    
    # Read file info
    file_infos = []
    for mp3_file in mp3_files:
        tags = get_mp3_tags(mp3_file)
        if tags:
            file_infos.append({
                'file': mp3_file,
                'artist': tags['artist'],
                'album': tags['album'],
                'genre': tags['genre'],
                'audio': tags['audio']
            })
    
    # Filter files with both artist and album
    valid_files = [fi for fi in file_infos if fi['artist'] and fi['album']]
    
    if not valid_files:
        print('No files with both artist and album tags found.')
        sys.exit(0)
    
    print(f'Processing {len(valid_files)} file(s) with artist and album tags...\n')
    
    # Group by artist+album to avoid duplicate searches
    unique_releases = {}
    for fi in valid_files:
        key = (fi['artist'].lower(), fi['album'].lower())
        if key not in unique_releases:
            unique_releases[key] = fi
    
    print(f'Fetching styles for {len(unique_releases)} unique release(s) from Discogs...\n')
    
    # Cache releases
    release_cache = {}
    for (artist, album), fi in unique_releases.items():
        print(f'  Searching: {fi["artist"]} - {fi["album"]}... ', end='', flush=True)
        release = search_discogs_release(fi['artist'], fi['album'])
        
        if release:
            styles = get_styles_from_release(release)
            release_cache[(artist, album)] = styles
            if styles:
                print(f'✓ ({"; ".join(styles)})')
            else:
                print('✓ (no styles found)')
        else:
            release_cache[(artist, album)] = []
            print('✗ (not found)')
    
    print('\nUpdating MP3 files...\n')
    
    updated = 0
    skipped = 0
    missing_tags = 0
    failed = 0
    
    for fi in file_infos:
        file_name = fi['file'].name
        
        if not fi['artist'] or not fi['album']:
            missing_tags += 1
            print(f'  {file_name}: Skipped (missing artist or album tag)')
            continue
        
        key = (fi['artist'].lower(), fi['album'].lower())
        styles = release_cache.get(key, [])
        
        if not styles:
            skipped += 1
            print(f'  {file_name}: No styles found for "{fi["artist"]} - {fi["album"]}"')
            continue
        
        # Replace genre with Discogs styles (always replace, don't append)
        new_genre = combine_genres(fi['genre'], styles)
        
        # Only skip if no styles were found (empty result)
        if not new_genre or new_genre == "":
            skipped += 1
            print(f'  {file_name}: No styles found for "{fi["artist"]} - {fi["album"]}"')
            continue
        
        # Update MP3 file
        if update_mp3_genre(fi['file'], fi['audio'], new_genre):
            updated += 1
            print(f'  ✓ {file_name}: "{new_genre}"')
        else:
            failed += 1
            print(f'  ✗ {file_name}: Failed to update genre')
    
    print(f'\n--- Summary ---')
    print(f'Updated: {updated}')
    print(f'Skipped (no styles found): {skipped}')
    print(f'Skipped (missing tags): {missing_tags}')
    print(f'Failed: {failed}')
    
    if failed > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
