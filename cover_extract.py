import os
import argparse
from mutagen.flac import FLAC
from mutagen.id3 import ID3, APIC, ID3NoHeaderError
from rich.console import Console

console = Console()
AUDIO_EXTS = [".flac", ".mp3"]

def is_valid_audio(filename):
    return not filename.startswith(("._", ".")) and any(filename.lower().endswith(ext) for ext in AUDIO_EXTS)

def extract_embedded_cover(audio_path, output_path, dry_run=False):
    try:
        if audio_path.lower().endswith(".flac"):
            audio = FLAC(audio_path)
            for pic in audio.pictures:
                if pic.type == 3:
                    if not dry_run:
                        with open(output_path, "wb") as f:
                            f.write(pic.data)
                    return True
        elif audio_path.lower().endswith(".mp3"):
            try:
                audio = ID3(audio_path)
            except ID3NoHeaderError:
                return False
            for tag in audio.values():
                if isinstance(tag, APIC) and tag.type == 3:
                    if not dry_run:
                        with open(output_path, "wb") as f:
                            f.write(tag.data)
                    return True
    except Exception as e:
        console.print(f"[red]Error extracting from {audio_path}: {e}[/red]")
    return False

def describe_folder(folder):
    parts = folder.strip(os.sep).split(os.sep)
    if len(parts) >= 3:
        return parts[-3], parts[-2], parts[-1]  # letter, artist, album
    elif len(parts) >= 2:
        return parts[-2], parts[-1], ""
    else:
        return "", parts[-1], ""

def process_album_folder(folder, dry_run=False):
    for filename in sorted(os.listdir(folder)):
        if is_valid_audio(filename):
            audio_path = os.path.join(folder, filename)
            cover_path = os.path.join(folder, "cover.jpg")
            return extract_embedded_cover(audio_path, cover_path, dry_run)
    return False

def scan_archive(root_path, dry_run=False, verbose=False):
    folders = []
    for dirpath, _, filenames in os.walk(root_path):
        if any(is_valid_audio(f) for f in filenames):
            folders.append(dirpath)

    total = len(folders)
    covers_extracted = 0

    for index, folder in enumerate(folders, 1):
        letter, artist, album = describe_folder(folder)
        console.print(f"\n[{index}/{total}] {letter} / {artist} / {album}", style="bold")
        success = process_album_folder(folder, dry_run)
        if success:
            msg = "cover.jpg saved" if not dry_run else "cover.jpg skipped (dry-run)"
            console.print(f"[green]✓ Embedded cover found — {msg}[/green]")
            covers_extracted += 1
        else:
            console.print(f"[yellow]– No embedded cover found[/yellow]")

    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Folders scanned: {total}")
    console.print(f"Covers extracted: {covers_extracted}")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract embedded cover art from audio files.")
    parser.add_argument("-d", "--directory", required=True, help="Root directory to scan")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without writing files")
    parser.add_argument("--verbose", action="store_true", help="Reserved for future verbosity toggle")
    args = parser.parse_args()
    scan_archive(args.directory, args.dry_run, args.verbose)