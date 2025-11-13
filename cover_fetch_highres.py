import os
import sys
import argparse
import subprocess
from pathlib import Path

# Auto-activate virtual environment
script_dir = Path(__file__).parent.parent
venv_python = script_dir / "hoarder_env" / "bin" / "python3"
if venv_python.exists() and sys.executable != str(venv_python):
    print("🔄 Auto-activating hoarder environment...")
    os.execv(str(venv_python), [str(venv_python)] + sys.argv)

from PIL import Image
from rich.console import Console

console = Console()
MIN_WIDTH = 1000
MIN_HEIGHT = 1000
AUDIO_EXTS = [".flac", ".mp3", ".m4a", ".ogg", ".wav"]

def is_audio_file(filename):
    return any(filename.lower().endswith(ext) for ext in AUDIO_EXTS)

def get_cover_dimensions(cover_path):
    try:
        with Image.open(cover_path) as img:
            return img.size
    except Exception:
        return (0, 0)

def find_audio_file(folder):
    for f in sorted(os.listdir(folder)):
        if is_audio_file(f):
            return os.path.join(folder, f)
    return None

def should_replace_cover(cover_path):
    if not os.path.exists(cover_path):
        return True
    width, height = get_cover_dimensions(cover_path)
    return width < MIN_WIDTH or height < MIN_HEIGHT

def describe_folder(folder):
    parts = folder.strip(os.sep).split(os.sep)
    if len(parts) >= 3:
        return parts[-3], parts[-2], parts[-1]
    elif len(parts) >= 2:
        return parts[-2], parts[-1], ""
    else:
        return "", parts[-1], ""

def process_album_folder(folder, dry_run=False):
    cover_path = os.path.join(folder, "cover.jpg")
    if should_replace_cover(cover_path):
        audio_file = find_audio_file(folder)
        if audio_file:
            if dry_run:
                return "Would launch COVIT"
            try:
                # Check if COVIT is available in the bin directory
                script_dir = Path(__file__).parent
                covit_path = script_dir / "bin" / "covit"
                if not covit_path.exists():
                    return f"COVIT not found at {covit_path}. Please install COVIT first."
                
                subprocess.run([
                    str(covit_path),
                    "--address", "covers.musichoarders.xyz",
                    "--input", audio_file,
                    "--query-sources", "applemusic,amazonmusic,bandcamp,deezer",
                    "--query-resolution", "1000",
                    "--primary-output", "cover",
                    "--primary-overwrite"
                ], cwd=folder)
                return "Cover fetched via COVIT"
            except Exception as e:
                return f"Error fetching cover: {e}"
        else:
            return "No audio file found"
    else:
        return "Cover already high-res"

def scan_archive(root_path, dry_run=False, verbose=False):
    folders = []
    for dirpath, _, filenames in os.walk(root_path):
        if any(is_audio_file(f) for f in filenames):
            folders.append(dirpath)

    total = len(folders)
    fetched = 0
    skipped = 0
    errors = 0

    for index, folder in enumerate(folders, 1):
        letter, artist, album = describe_folder(folder)
        console.print(f"\n[{index}/{total}] {letter} / {artist} / {album}", style="bold")
        result = process_album_folder(folder, dry_run)

        if "Cover fetched" in result:
            console.print(f"[green]{result}[/green]")
            fetched += 1
        elif "already high-res" in result:
            console.print(f"[cyan]{result}[/cyan]")
            skipped += 1
        elif "Would launch" in result:
            console.print(f"[yellow]{result}[/yellow]")
            skipped += 1
        else:
            console.print(f"[red]{result}[/red]")
            errors += 1

    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Folders scanned: {total}")
    console.print(f"Covers fetched: {fetched}")
    console.print(f"Skipped (high-res or dry-run): {skipped}")
    console.print(f"Errors: {errors}")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch high-res cover art using COVIT.")
    parser.add_argument("-d", "--directory", help="Root directory to scan")
    parser.add_argument("--archive", help="Archive directory to scan (alternative to -d)")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without launching COVIT")
    parser.add_argument("--verbose", action="store_true", help="Reserved for future verbosity toggle")
    args = parser.parse_args()
    
    # Determine the directory to scan
    target_dir = args.directory or args.archive
    if not target_dir:
        print("❌ Error: Please specify a directory with -d or --archive")
        sys.exit(1)
        
    scan_archive(target_dir, args.dry_run, args.verbose)