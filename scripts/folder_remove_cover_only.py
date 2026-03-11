#!/usr/bin/env python3
"""
clean_empty_folders.py - Detect and optionally remove folders that are empty
or only contain cover images (cover.jpg, folder.jpg, etc.).
"""

import os
import argparse
from pathlib import Path
from rich.console import Console

console = Console()

# Common cover image filenames (case-insensitive)
COVER_NAMES = {
    "cover.jpg", "cover.jpeg", "cover.png", "cover.webp",
    "folder.jpg", "folder.jpeg", "folder.png", "folder.webp",
    "album cover.jpg", "album cover.jpeg",
    "albumartsmall.jpg", "artist.jpg"
}

def is_cover_file(filename):
    """Check if a file is a cover image."""
    return filename.lower() in COVER_NAMES

def is_empty_or_cover_only(folder_path):
    """
    Check if folder is empty or only contains cover images.
    Returns (is_empty_or_cover_only, contents_list).
    """
    try:
        contents = list(Path(folder_path).iterdir())
        if not contents:
            return True, []
        
        # Check if all items are cover images
        non_cover = []
        for item in contents:
            if item.is_dir():
                # If there are subdirectories, it's not empty
                return False, contents
            if not is_cover_file(item.name):
                non_cover.append(item.name)
        
        # If all files are cover images, it's considered empty
        return len(non_cover) == 0, [item.name for item in contents]
    except PermissionError:
        return None, []  # Can't access, skip

def scan_and_clean(root, dry_run=False, verbose=False, delete_covers=False):
    """
    Scan directory tree for empty folders or folders with only cover images.
    """
    root_path = Path(root)
    empty_folders = []
    cover_only_folders = []
    total_scanned = 0
    
    # Walk through all directories (bottom-up to handle nested empty folders)
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        total_scanned += 1
        folder_path = Path(dirpath)
        
        # Skip if it's the root directory itself
        if folder_path == root_path:
            continue
        
        is_empty, contents = is_empty_or_cover_only(dirpath)
        
        if is_empty is None:
            # Permission error, skip
            continue
        
        if is_empty:
            if not contents:
                empty_folders.append((dirpath, []))
                if verbose:
                    console.print(f"[yellow]Empty folder:[/yellow] {dirpath}")
            else:
                cover_only_folders.append((dirpath, contents))
                if verbose:
                    cover_list = ", ".join(contents)
                    console.print(f"[yellow]Cover-only folder:[/yellow] {dirpath} ({cover_list})")
    
    # Remove folders
    deleted_empty = 0
    deleted_cover_only = 0
    deleted_covers = 0
    
    # Process empty folders first
    for folder_path, _ in empty_folders:
        if dry_run:
            console.print(f"[cyan]Would delete empty folder:[/cyan] {folder_path}")
        else:
            try:
                os.rmdir(folder_path)
                deleted_empty += 1
                if verbose:
                    console.print(f"[green]✓ Deleted empty folder:[/green] {folder_path}")
            except OSError as e:
                console.print(f"[red]Could not delete {folder_path}: {e}[/red]")
    
    # Process cover-only folders
    for folder_path, contents in cover_only_folders:
        if dry_run:
            cover_list = ", ".join(contents)
            console.print(f"[cyan]Would delete cover-only folder:[/cyan] {folder_path} ({cover_list})")
            if delete_covers:
                for cover in contents:
                    console.print(f"  [cyan]Would delete cover:[/cyan] {os.path.join(folder_path, cover)}")
        else:
            # Delete cover files if requested
            if delete_covers:
                for cover in contents:
                    try:
                        cover_path = os.path.join(folder_path, cover)
                        os.remove(cover_path)
                        deleted_covers += 1
                        if verbose:
                            console.print(f"[green]✓ Deleted cover:[/green] {cover_path}")
                    except Exception as e:
                        console.print(f"[red]Could not delete {cover_path}: {e}[/red]")
            
            # Delete the folder itself
            try:
                os.rmdir(folder_path)
                deleted_cover_only += 1
                if verbose:
                    console.print(f"[green]✓ Deleted cover-only folder:[/green] {folder_path}")
            except OSError as e:
                console.print(f"[red]Could not delete {folder_path}: {e}[/red]")
    
    # Summary
    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Folders scanned: {total_scanned}")
    console.print(f"Empty folders found: {len(empty_folders)}")
    console.print(f"Cover-only folders found: {len(cover_only_folders)}")
    if not dry_run:
        console.print(f"Empty folders deleted: {deleted_empty}")
        console.print(f"Cover-only folders deleted: {deleted_cover_only}")
        if delete_covers:
            console.print(f"Cover files deleted: {deleted_covers}")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Detect and optionally remove folders that are empty or only contain cover images."
    )
    parser.add_argument("-d", "--directory", required=True, help="Root directory to scan")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without modifying files")
    parser.add_argument("--verbose", action="store_true", help="Print detailed output per folder")
    parser.add_argument(
        "--delete-covers",
        action="store_true",
        help="Delete cover images before removing folders (only for cover-only folders)"
    )
    args = parser.parse_args()
    
    scan_and_clean(args.directory, args.dry_run, args.verbose, args.delete_covers)

