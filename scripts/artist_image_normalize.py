#!/usr/bin/env python3
"""
Normalize artist folder images:
- rename folder.jpg to artist.jpg
- if both exist, remove folder.jpg
"""

import argparse
import os
from pathlib import Path

from rich.console import Console


console = Console()
AUDIO_EXTENSIONS = {".flac", ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".aif", ".aiff"}


def is_artist_folder(path: Path) -> bool:
    try:
        filenames = [item.name for item in path.iterdir() if item.is_file()]
    except PermissionError:
        return False

    if not any(name.lower() in {"folder.jpg", "artist.jpg"} for name in filenames):
        return False

    return not any(Path(name).suffix.lower() in AUDIO_EXTENSIONS for name in filenames)


def normalize_artist_image_folder(folder: Path, dry_run=False):
    folder_image = folder / "folder.jpg"
    artist_image = folder / "artist.jpg"

    if not folder_image.exists():
        return "clean"

    if artist_image.exists():
        if dry_run:
            return "would_delete_duplicate"
        folder_image.unlink()
        return "deleted_duplicate"

    if dry_run:
        return "would_rename"

    folder_image.rename(artist_image)
    return "renamed"


def describe_folder(folder):
    parts = str(folder).strip(os.sep).split(os.sep)
    if len(parts) >= 3:
        return parts[-3], parts[-2], parts[-1]
    if len(parts) >= 2:
        return parts[-2], parts[-1], ""
    return "", parts[-1], ""


def scan_archive(root, dry_run=False, verbose=False):
    candidate_folders = []
    for dirpath, _, _ in os.walk(root):
        folder = Path(dirpath)
        if is_artist_folder(folder):
            candidate_folders.append(folder)

    renamed = 0
    deleted = 0

    for index, folder in enumerate(candidate_folders, 1):
        letter, artist, album = describe_folder(folder)
        console.print(f"\n[{index}/{len(candidate_folders)}] {letter} / {artist} / {album}", style="bold")

        result = normalize_artist_image_folder(folder, dry_run=dry_run)
        if result == "renamed":
            renamed += 1
            console.print("[green]Renamed folder.jpg -> artist.jpg[/green]")
        elif result == "deleted_duplicate":
            deleted += 1
            console.print("[green]Deleted duplicate folder.jpg[/green]")
        elif result == "would_rename":
            renamed += 1
            console.print("[yellow]Would rename folder.jpg -> artist.jpg[/yellow]")
        elif result == "would_delete_duplicate":
            deleted += 1
            console.print("[yellow]Would delete duplicate folder.jpg[/yellow]")
        elif verbose:
            console.print("[cyan]No changes needed[/cyan]")

    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Artist folders scanned: {len(candidate_folders)}")
    console.print(f"Folder images renamed: {renamed}")
    console.print(f"Duplicate folder images removed: {deleted}")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")


def main():
    parser = argparse.ArgumentParser(
        description="Rename artist folder.jpg images to artist.jpg and remove duplicates."
    )
    parser.add_argument("-d", "--directory", required=True, help="Root directory to scan")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without modifying files")
    parser.add_argument("--verbose", action="store_true", help="Print folders with no changes")
    args = parser.parse_args()

    scan_archive(args.directory, dry_run=args.dry_run, verbose=args.verbose)


if __name__ == "__main__":
    main()
