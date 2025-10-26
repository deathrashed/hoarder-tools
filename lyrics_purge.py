import os
import argparse
import shutil
from rich.console import Console

console = Console()

def purge_lyrics_folders(root, dry_run=False, verbose=False):
    scanned = 0
    removed = 0
    errors = 0

    for dirpath, dirnames, _ in os.walk(root, topdown=False):
        for dirname in dirnames:
            if dirname.lower() == "lyrics":
                scanned += 1
                full_path = os.path.join(dirpath, dirname)
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
    console.print(f"Lyrics folders found: {scanned}")
    console.print(f"Lyrics folders deleted: {removed}")
    console.print(f"Errors: {errors}")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Purge all 'Lyrics' folders from the archive.")
    parser.add_argument("-d", "--directory", required=True, help="Root directory to scan")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without deleting folders")
    parser.add_argument("--verbose", action="store_true", help="Print each deletion")
    args = parser.parse_args()
    purge_lyrics_folders(args.directory, args.dry_run, args.verbose)