#!/usr/bin/env python3
"""
normalize_multi_artist.py - Normalizes ARTIST and TITLE tags so only the first artist
remains in ARTIST and additional artists are appended to TITLE as (feat. ...).
"""

import os
import re
import argparse
from pathlib import Path
from typing import List
from mutagen.id3 import ID3, ID3NoHeaderError, TPE1, TIT2
from rich.console import Console

console = Console()


def split_artists(raw: str) -> List[str]:
    """Split artist string into individual artists."""
    if not raw:
        return []
    
    # Split on ";", "," or " / " or " & " or " feat. " / " ft. "
    tokens = re.split(r';\s*|,\s*|\s/\s|\s&\s|\sfeat\.?\s|\sft\.?\s', raw, flags=re.IGNORECASE)
    tokens = [t.strip() for t in tokens if t.strip()]
    
    # If no delimiters found, keep as single artist
    if not tokens and raw.strip():
        tokens = [raw.strip()]
    
    # Deduplicate while preserving order (case-insensitive)
    seen = set()
    out = []
    for t in tokens:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            out.append(t)
    
    return out


def format_feat(additional: List[str]) -> str:
    """Format additional artists as (feat. ...)."""
    if not additional:
        return ""
    if len(additional) == 1:
        return f"(feat. {additional[0]})"
    if len(additional) == 2:
        return f"(feat. {additional[0]} & {additional[1]})"
    
    head = ", ".join(additional[:-1])
    last = additional[-1]
    return f"(feat. {head} & {last})"


def title_has_feat(title: str) -> bool:
    """Check if title already has a (feat. ...) tag."""
    if not title:
        return False
    return bool(re.search(r'\(feat\.?[^)]*\)', title, re.IGNORECASE))


def escape_regex(s: str) -> str:
    """Escape special regex characters."""
    return re.escape(s)


def normalize_metadata(file_path: str, dry_run: bool = False) -> dict:
    """Normalize metadata for a single MP3 file."""
    result = {
        "file": file_path,
        "before_artist": "",
        "after_artist": "",
        "before_title": "",
        "after_title": "",
        "changed": False,
        "reason": None
    }
    
    try:
        # Read tags
        try:
            tags = ID3(file_path)
        except ID3NoHeaderError:
            tags = ID3()
        
        # Get artist
        artist_frames = tags.getall("TPE1")
        before_artist = str(artist_frames[0]) if artist_frames else ""
        result["before_artist"] = before_artist
        
        # Get title
        title_frames = tags.getall("TIT2")
        if title_frames:
            before_title = str(title_frames[0])
        else:
            # Fallback to filename without extension
            before_title = Path(file_path).stem
        result["before_title"] = before_title
        
        # Split artists
        artists = split_artists(before_artist)
        if not artists:
            result["reason"] = "No ARTIST tag"
            return result
        
        # Primary artist is first
        primary = artists[0]
        
        # Additional artists (excluding primary, case-insensitive)
        additional_raw = [
            a for a in artists[1:]
            if a.lower() != primary.lower()
        ]
        
        # Avoid duplicating names if already present in title
        to_add = []
        for a in additional_raw:
            # Check if artist name is already in title (word boundary match)
            pattern = re.compile(rf"\b{escape_regex(a)}\b", re.IGNORECASE)
            if not pattern.search(before_title):
                to_add.append(a)
        
        # Build new title
        after_title = before_title
        if to_add and not title_has_feat(before_title):
            feat_str = format_feat(to_add)
            after_title = f"{before_title} {feat_str}"
        
        after_artist = primary
        
        # Check if changes are needed
        changed = (after_artist != before_artist) or (after_title != before_title)
        result["changed"] = changed
        result["after_artist"] = after_artist
        result["after_title"] = after_title
        
        # Update tags if changed and not dry run
        if changed and not dry_run:
            try:
                # Remove old artist and title tags
                tags.delall("TPE1")
                tags.delall("TIT2")
                
                # Add new tags
                tags.add(TPE1(encoding=3, text=after_artist))
                tags.add(TIT2(encoding=3, text=after_title))
                
                tags.save(file_path)
            except Exception as e:
                result["reason"] = f"Update failed: {e}"
                result["changed"] = False
                result["after_artist"] = before_artist
                result["after_title"] = before_title
        
    except Exception as e:
        result["reason"] = f"Error: {str(e)}"
    
    return result


def scan_directory(directory: str, dry_run: bool = False, verbose: bool = False):
    """Scan directory for MP3 files and normalize metadata."""
    directory_path = Path(directory)
    mp3_files = list(directory_path.rglob("*.mp3"))
    
    if not mp3_files:
        console.print(f"[yellow]No MP3 files found in: {directory}[/yellow]")
        return
    
    console.print(f"[bold]Found {len(mp3_files)} MP3 files[/bold]")
    
    results = []
    for mp3_file in mp3_files:
        result = normalize_metadata(str(mp3_file), dry_run)
        results.append(result)
        
        if verbose and result["changed"]:
            console.print(f"[green]Updated:[/green] {os.path.basename(result['file'])}")
            console.print(f"  Artist: '{result['before_artist']}' -> '{result['after_artist']}'")
            console.print(f"  Title: '{result['before_title']}' -> '{result['after_title']}'")
        elif verbose and result["reason"]:
            console.print(f"[yellow]Skipped:[/yellow] {os.path.basename(result['file'])} - {result['reason']}")
    
    # Summary
    changed = [r for r in results if r["changed"]]
    failed = [r for r in results if r["reason"] and not r["changed"] and r["reason"] != "No ARTIST tag"]
    skipped = [r for r in results if not r["changed"] and r not in failed]
    
    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Processed: {len(results)}")
    console.print(f"Updated: {len(changed)}")
    console.print(f"Skipped: {len(skipped)}")
    console.print(f"Failed: {len(failed)}")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")
    
    # Show some examples
    if changed and verbose:
        console.print("\n[bold]Updated Files (first 10):[/bold]")
        for r in changed[:10]:
            console.print(f"  [green]{os.path.basename(r['file'])}[/green]")
            console.print(f"    Artist: '{r['before_artist']}' -> '{r['after_artist']}'")
            console.print(f"    Title: '{r['before_title']}' -> '{r['after_title']}'")
        if len(changed) > 10:
            console.print(f"  ...and {len(changed) - 10} more")
    
    if failed and verbose:
        console.print("\n[bold]Failed:[/bold]")
        for r in failed[:10]:
            console.print(f"  [red]{os.path.basename(r['file'])}[/red] - {r['reason']}")
        if len(failed) > 10:
            console.print(f"  ...and {len(failed) - 10} more")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Normalize multi-artist metadata in MP3 files."
    )
    parser.add_argument("-d", "--directory", required=True, help="Directory containing MP3 files")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without modifying files")
    parser.add_argument("--verbose", action="store_true", help="Print detailed output")
    args = parser.parse_args()
    
    scan_directory(args.directory, args.dry_run, args.verbose)

