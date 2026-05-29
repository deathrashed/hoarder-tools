#!/usr/bin/env python3
"""
mp3_genres_from_lastfm.py - Replaces the Genre field of MP3 files with the top two Last.fm artist tags.
"""

import os
import re
import argparse
import time
from pathlib import Path
from typing import List
from mutagen.id3 import ID3, ID3NoHeaderError
from rich.console import Console
import requests

console = Console()

# Genre expansion scheme
GENRE_EXPANSIONS = {
    "thrash": "Thrash Metal",
    "death": "Death Metal",
    "black": "Black Metal",
    "doom": "Doom Metal",
    "heavy": "Heavy Metal",
    "hardcore": "Hardcore",
    "punk": "Punk Rock",
    "folk": "Folk Metal",
    "progressive": "Progressive Metal",
    "power": "Power Metal",
    "symphonic": "Symphonic Metal",
    "sludge": "Sludge Metal",
    "stoner": "Stoner Rock",
    "speed": "Speed Metal",
    "gothic": "Gothic Metal",
    "groove": "Groove Metal",
    "funk": "Funk Metal",
    "alternative": "Alternative Rock",
    "indie": "Indie Rock",
    "industrial": "Industrial",
    "math": "Mathcore",
    "horror": "Horror Punk",
}

SLASH_EXPANSIONS = {
    "death/thrash": ["Death/Thrash", "Death Metal", "Thrash Metal"],
    "thrash/death": ["Thrash/Death", "Thrash Metal", "Death Metal"],
    "death/doom": ["Death/Doom", "Death Metal", "Doom Metal"],
    "doom/death": ["Doom/Death", "Doom Metal", "Death Metal"],
    "black/death": ["Black/Death", "Black Metal", "Death Metal"],
    "death/black": ["Death/Black", "Death Metal", "Black Metal"],
    "black/thrash": ["Black/Thrash", "Black Metal", "Thrash Metal"],
    "thrash/black": ["Thrash/Black", "Thrash Metal", "Black Metal"],
    "progressive death/thrash": ["Progressive Death/Thrash", "Progressive Metal", "Death Metal", "Thrash Metal"],
    "blackened death/thrash": ["Blackened Death/Thrash", "Black Metal", "Death Metal", "Thrash Metal"],
}

COMPOUND_EXPANSIONS = {
    "crossover thrash": ["Crossover", "Thrash Metal"],
    "thrash crossover": ["Thrash Metal", "Crossover"],
    "beatdown hardcore": ["Beatdown", "Hardcore"],
    "hardcore beatdown": ["Hardcore", "Beatdown"],
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
}

COMMON_GENRE_WORDS = {
    "metal", "rock", "punk", "hardcore", "core", "thrash", "death",
    "black", "doom", "folk", "progressive", "power", "symphonic",
    "alternative", "classic", "heavy", "beatdown", "crossover",
    "sludge", "stoner", "speed", "gothic", "groove", "funk", "indie",
    "industrial", "math", "horror", "grindcore", "deathcore", "mathcore",
    "post", "new", "nu", "glam", "technical", "brutal", "slamming",
    "viking", "war", "atmospheric", "avantgarde", "blackened"
}

BLOCKED_TAGS = {"seen live"}


def to_mixed_case(tag: str) -> str:
    """Capitalize first letter of each word while preserving separators."""
    if not tag:
        return ""
    lower = tag.lower().strip()
    # Capitalize first letter of each word
    cased = re.sub(r"\b([a-z])([a-z0-9'&]*)\b", lambda m: m.group(1).upper() + m.group(2), lower)
    return re.sub(r"\s+", " ", cased).strip()


def expand_genre(genre: str) -> List[str]:
    """Expand a single genre according to the expansion scheme."""
    lower = genre.lower().strip()
    expanded = []
    
    # Check for slash notation first
    if lower in SLASH_EXPANSIONS:
        return SLASH_EXPANSIONS[lower]
    
    # Check for known compound expansions
    if lower in COMPOUND_EXPANSIONS:
        return COMPOUND_EXPANSIONS[lower]
    
    # Handle slash notation pattern (Genre1/Genre2)
    slash_match = re.match(r"^(.+?)/(.+)$", lower)
    if slash_match:
        part1, part2 = slash_match.groups()
        genre1 = to_mixed_case(part1.strip())
        genre2 = to_mixed_case(part2.strip())
        combined = to_mixed_case(f"{part1.strip()}/{part2.strip()}")
        
        # Expand each part recursively
        expanded1 = expand_genre(genre1)
        expanded2 = expand_genre(genre2)
        
        # Combine results
        expanded.append(combined)
        expanded.extend(expanded1)
        expanded.extend(expanded2)
        return unique_case_insensitive(expanded)
    
    # Handle compound words
    words = lower.split()
    if len(words) >= 2:
        last_word = words[-1]
        if last_word in COMMON_GENRE_WORDS and len(words) == 2:
            first_part = to_mixed_case(words[0])
            expanded_second = GENRE_EXPANSIONS.get(last_word, to_mixed_case(last_word))
            expanded.append(first_part)
            expanded.append(expanded_second)
            return unique_case_insensitive(expanded)
    
    # Check if it's a single genre term that should be expanded
    if lower in GENRE_EXPANSIONS:
        return [GENRE_EXPANSIONS[lower]]
    
    # Default: return the genre as-is (properly cased)
    return [to_mixed_case(genre)]


def unique_case_insensitive(arr: List[str]) -> List[str]:
    """Remove duplicates case-insensitively while preserving order."""
    seen = set()
    out = []
    for v in arr:
        key = v.lower()
        if key not in seen:
            seen.add(key)
            out.append(v)
    return out


def remove_redundant_genres(genres: List[str]) -> List[str]:
    """Remove redundant genres (e.g., 'Rock' when 'Hard Rock' is present)."""
    if len(genres) <= 1:
        return genres
    
    filtered = []
    lower_genres = [g.lower() for g in genres]
    
    for i, current in enumerate(genres):
        current_lower = lower_genres[i]
        is_redundant = False
        
        # Don't remove slash notation genres
        if "/" in current:
            filtered.append(current)
            continue
        
        # Check if this genre is contained in any other genre
        for j, other in enumerate(genres):
            if i == j:
                continue
            
            other_lower = lower_genres[j]
            
            # Skip slash notation when checking
            if "/" in other:
                continue
            
            # If the other genre is longer and contains this genre, this one is redundant
            if len(other) > len(current):
                escaped_current = re.escape(current_lower)
                
                # For multi-word genres, match as whole phrase
                if " " in current_lower:
                    pattern = re.compile(rf"(^|\s){escaped_current}(\s|$)", re.IGNORECASE)
                else:
                    pattern = re.compile(rf"\b{escaped_current}\b", re.IGNORECASE)
                
                if pattern.search(other_lower):
                    is_redundant = True
                    break
        
        if not is_redundant:
            filtered.append(current)
    
    return filtered


def expand_genres(genres: List[str]) -> List[str]:
    """Expand a list of genres and combine intelligently."""
    all_expanded = []
    
    # Expand each genre
    for genre in genres:
        expanded = expand_genre(genre)
        all_expanded.extend(expanded)
    
    # Get unique expanded genres
    unique_expanded = unique_case_insensitive(all_expanded)
    lower_expanded = [g.lower() for g in unique_expanded]
    
    # Special handling: automatically combine related genres
    has_death_metal = "death metal" in lower_expanded
    has_doom_metal = "doom metal" in lower_expanded
    has_death_doom_slash = any("death/doom" in g or "doom/death" in g for g in lower_expanded)
    if has_death_metal and has_doom_metal and not has_death_doom_slash:
        unique_expanded.insert(0, "Death/Doom")
    
    has_thrash_metal = "thrash metal" in lower_expanded
    has_death_metal2 = "death metal" in lower_expanded
    has_death_thrash_slash = any("death/thrash" in g or "thrash/death" in g for g in lower_expanded)
    if has_thrash_metal and has_death_metal2 and not has_death_thrash_slash:
        unique_expanded.insert(0, "Death/Thrash")
    
    has_black_metal = "black metal" in lower_expanded
    has_thrash_metal2 = "thrash metal" in lower_expanded
    has_black_thrash_slash = any("black/thrash" in g or "thrash/black" in g for g in lower_expanded)
    if has_black_metal and has_thrash_metal2 and not has_black_thrash_slash:
        unique_expanded.insert(0, "Black/Thrash")
    
    has_black_metal2 = "black metal" in lower_expanded
    has_death_metal3 = "death metal" in lower_expanded
    has_black_death_slash = any("black/death" in g or "death/black" in g for g in lower_expanded)
    if has_black_metal2 and has_death_metal3 and not has_black_death_slash:
        unique_expanded.insert(0, "Black/Death")
    
    return remove_redundant_genres(unique_expanded)


def fetch_top_tags(artist: str, api_key: str, max_tags: int = 2) -> List[str]:
    """Fetch top tags for artist from Last.fm API with retry logic."""
    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "artist.gettoptags",
        "artist": artist,
        "api_key": api_key,
        "format": "json"
    }
    
    attempts = 0
    delay = 0.6  # seconds
    
    while attempts < 4:
        try:
            time.sleep(0.3)  # Rate limiting
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                tags = data.get("toptags", {}).get("tag", [])
                
                if not tags:
                    return []
                
                # Normalize to list
                if not isinstance(tags, list):
                    tags = [tags]
                
                # Filter out blocked tags and sort by count
                cleaned = []
                for t in tags:
                    name = t.get("name", "")
                    if name and name.lower() not in BLOCKED_TAGS:
                        cleaned.append({
                            "name": name,
                            "count": int(t.get("count", "0") or "0")
                        })
                
                # Sort by count descending
                cleaned.sort(key=lambda x: x["count"], reverse=True)
                
                # Take top max_tags and convert to mixed case
                return [to_mixed_case(t["name"]) for t in cleaned[:max_tags]]
            
            elif response.status_code == 429 or (500 <= response.status_code < 600):
                # Rate limited or server error - retry
                attempts += 1
                time.sleep(delay)
                delay *= 2
                continue
            else:
                # Other errors - don't retry
                return []
                
        except Exception as e:
            console.print(f"[yellow]Error fetching tags for {artist}: {e}[/yellow]")
            attempts += 1
            if attempts < 4:
                time.sleep(delay)
                delay *= 2
    
    return []


def get_artist_from_mp3(file_path: str) -> str:
    """Get artist tag from MP3 file."""
    try:
        tags = ID3(file_path)
        artist_frames = tags.getall("TPE1")  # TPE1 is Artist frame
        if artist_frames:
            return str(artist_frames[0])
    except (ID3NoHeaderError, Exception):
        pass
    return ""


def update_genre(file_path: str, genre: str) -> bool:
    """Update genre tag in MP3 file."""
    try:
        try:
            tags = ID3(file_path)
        except ID3NoHeaderError:
            tags = ID3()
        
        # Remove existing genre tags
        tags.delall("TCON")
        
        # Add new genre tag
        from mutagen.id3 import TCON
        tags.add(TCON(encoding=3, text=genre))
        tags.save(file_path)
        return True
    except Exception as e:
        console.print(f"[red]Failed to update {file_path}: {e}[/red]")
        return False


def scan_directory(directory: str, api_key: str, dry_run: bool = False, verbose: bool = False):
    """Scan directory for MP3 files and update genres."""
    directory_path = Path(directory)
    mp3_files = list(directory_path.rglob("*.mp3"))
    
    if not mp3_files:
        console.print(f"[yellow]No MP3 files found in: {directory}[/yellow]")
        return
    
    console.print(f"[bold]Found {len(mp3_files)} MP3 files[/bold]")
    
    # First pass: collect artists
    file_infos = []
    for mp3_file in mp3_files:
        artist = get_artist_from_mp3(str(mp3_file))
        if artist:
            file_infos.append({"file": str(mp3_file), "artist": artist})
    
    # Get unique artists
    unique_artists = unique_case_insensitive([fi["artist"] for fi in file_infos])
    
    console.print(f"[bold]Fetching tags for {len(unique_artists)} unique artist(s) from Last.fm...[/bold]")
    
    # Cache tags per artist
    artist_cache = {}
    for artist in unique_artists:
        tags = fetch_top_tags(artist, api_key, max_tags=2)
        artist_cache[artist.lower()] = tags
        if verbose:
            console.print(f"[cyan]Artist: {artist} -> Tags: {tags}[/cyan]")
    
    # Second pass: update files
    updated = 0
    skipped = 0
    missing_artist = 0
    failed = 0
    
    for file_info in file_infos:
        file_path = file_info["file"]
        artist = file_info["artist"]
        file_name = os.path.basename(file_path)
        
        if not artist:
            missing_artist += 1
            if verbose:
                console.print(f"[yellow]Skipped {file_name}: No artist tag[/yellow]")
            continue
        
        top_tags = artist_cache.get(artist.lower(), [])
        if not top_tags:
            skipped += 1
            if verbose:
                console.print(f"[yellow]Skipped {file_name}: No top tags found for '{artist}'[/yellow]")
            continue
        
        # Expand genres
        expanded_genres = expand_genres(top_tags)
        final_genre = "; ".join(expanded_genres)
        
        if dry_run:
            console.print(f"[green]Would update {file_name}: Genre -> '{final_genre}'[/green]")
            updated += 1
        else:
            if update_genre(file_path, final_genre):
                updated += 1
                if verbose:
                    console.print(f"[green]Updated {file_name}: Genre -> '{final_genre}'[/green]")
            else:
                failed += 1
    
    # Summary
    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Audio files scanned: {len(mp3_files)}")
    console.print(f"Genres updated: {updated}")
    console.print(f"Skipped (no/empty top tags): {skipped}")
    console.print(f"Skipped (no artist tag): {missing_artist}")
    console.print(f"Failed: {failed}")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Replace Genre field of MP3 files with top two Last.fm artist tags."
    )
    parser.add_argument("-d", "--directory", required=True, help="Directory containing MP3 files")
    parser.add_argument("--api-key", help="Last.fm API key (or set LASTFM_API_KEY env var)")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without modifying files")
    parser.add_argument("--verbose", action="store_true", help="Print detailed output")
    args = parser.parse_args()
    
    # Get API key from arg or env var
    api_key = args.api_key or os.getenv("LASTFM_API_KEY")
    if not api_key:
        console.print("[red]Error: Last.fm API key required.[/red]")
        console.print("[yellow]Either use --api-key or set LASTFM_API_KEY environment variable[/yellow]")
        console.print("[yellow]Get your API key: https://www.last.fm/api/account/create[/yellow]")
        exit(1)
    
    scan_directory(args.directory, api_key, args.dry_run, args.verbose)

