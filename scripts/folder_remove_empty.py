import os
import argparse
import shutil
from rich.console import Console

console = Console()

AUDIO_EXTENSIONS = {".flac", ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".aif", ".aiff"}

def contains_audio_files(folder):
    for root, _, files in os.walk(folder):
        for f in files:
            if os.path.splitext(f)[1].lower() in AUDIO_EXTENSIONS:
                return True
    return False

def prune_empty_folders(root, dry_run=False, verbose=False):
    scanned = 0
    removed = 0
    errors = 0

    for dirpath, dirnames, _ in os.walk(root, topdown=False):
        for dirname in dirnames:
            full_path = os.path.join(dirpath, dirname)
            scanned += 1
            if os.path.isdir(full_path) and not contains_audio_files(full_path):
                if dry_run:
                    console.print(f"[yellow]Would delete:[/yellow] {full_path}")
                    continue
                try:
                    shutil.rmtree(full_path)
                    if verbose:
                        console.print(f"[green]Deleted:[/green] {full_path}")
                    removed += 1
                except Exception as e:
                    console.print(f"[red]Error deleting {full_path}: {e}[/red]")
                    errors += 1

    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Folders scanned: {scanned}")
    console.print(f"Folders deleted: {removed}")
    console.print(f"Errors: {errors}")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete folders that contain no audio files.")
    parser.add_argument("-d", "--directory", required=True, help="Root directory to scan")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without deleting folders")
    parser.add_argument("--verbose", action="store_true", help="Print each deletion")
    args = parser.parse_args()
    prune_empty_folders(args.directory, args.dry_run, args.verbose)