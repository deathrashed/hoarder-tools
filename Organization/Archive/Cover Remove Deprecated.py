import os
import argparse
from rich.console import Console

console = Console()

PURGE_EXTENSIONS = [".jp2", ".jxl"]

def purge_images(root, extensions, dry_run=False, verbose=False):
    total = 0
    deleted = 0
    errors = 0

    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if any(f.lower().endswith(ext) for ext in extensions):
                total += 1
                full_path = os.path.join(dirpath, f)
                if dry_run:
                    console.print(f"[yellow]Would delete:[/yellow] {full_path}")
                    continue
                try:
                    os.remove(full_path)
                    if verbose:
                        console.print(f"[green]Deleted:[/green] {full_path}")
                    deleted += 1
                except Exception as e:
                    console.print(f"[red]Error deleting {full_path}: {e}[/red]")
                    errors += 1

    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Files matched: {total}")
    console.print(f"Files deleted: {deleted}")
    console.print(f"Errors: {errors}")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Purge deprecated image formats (.jp2, .jxl).")
    parser.add_argument("-d", "--directory", required=True, help="Root directory to scan")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without deleting files")
    parser.add_argument("--verbose", action="store_true", help="Print each deletion")
    args = parser.parse_args()
    purge_images(args.directory, PURGE_EXTENSIONS, args.dry_run, args.verbose)