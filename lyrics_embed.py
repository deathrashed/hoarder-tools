import os
import re
import argparse
from mutagen.flac import FLAC
from mutagen.id3 import USLT, ID3, ID3NoHeaderError
from rich.console import Console

console = Console()
AUDIO_EXTS = [".flac", ".mp3"]

def strip_timestamps(text):
    return re.sub(r"\[\d{1,2}:\d{2}(?:\.\d{1,2})?\]", "", text).strip()

def find_lrc(audio_path):
    base = os.path.splitext(os.path.basename(audio_path))[0]
    folder = os.path.dirname(audio_path)
    candidates = [
        os.path.join(folder, f"{base}.lrc"),
        os.path.join(folder, "Lyrics", f"{base}.lrc")
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None

def has_embedded_lyrics(audio_path):
    """Check if file already has embedded lyrics."""
    try:
        if audio_path.lower().endswith(".flac"):
            audio = FLAC(audio_path)
            return "LYRICS" in audio
        elif audio_path.lower().endswith(".mp3"):
            tags = ID3(audio_path)
            return any(isinstance(tag, USLT) for tag in tags.values())
    except Exception:
        return False
    return False

def embed_lyrics(audio_path, lrc_path, dry_run=False):
    try:
        with open(lrc_path, "r", encoding="utf-8") as f:
            lyrics = strip_timestamps(f.read())
        if dry_run:
            return True
        if audio_path.lower().endswith(".flac"):
            audio = FLAC(audio_path)
            audio["LYRICS"] = lyrics
            audio.save()
        elif audio_path.lower().endswith(".mp3"):
            try:
                tags = ID3(audio_path)
            except ID3NoHeaderError:
                tags = ID3()
            tags.add(USLT(encoding=3, lang="eng", desc="", text=lyrics))
            tags.save(audio_path)
        return True
    except Exception as e:
        console.print(f"[red]Failed to embed: {audio_path} — {e}[/red]")
        return False

def describe_folder(folder):
    parts = folder.strip(os.sep).split(os.sep)
    if len(parts) >= 3:
        return parts[-3], parts[-2], parts[-1]
    elif len(parts) >= 2:
        return parts[-2], parts[-1], ""
    else:
        return "", parts[-1], ""

def scan_archive(root, dry_run=False, verbose=False):
    total = 0
    embedded = 0
    already_embedded = 0
    lrc_deleted = 0
    folders = []

    for dirpath, _, filenames in os.walk(root):
        if any(f.lower().endswith(tuple(AUDIO_EXTS)) for f in filenames):
            folders.append(dirpath)

    for index, folder in enumerate(folders, 1):
        letter, artist, album = describe_folder(folder)
        console.print(f"\n[{index}/{len(folders)}] {letter} / {artist} / {album}", style="bold")

        for file in sorted(os.listdir(folder)):
            if not any(file.lower().endswith(ext) for ext in AUDIO_EXTS):
                continue
            total += 1
            audio_path = os.path.join(folder, file)
            lrc_path = find_lrc(audio_path)

            if has_embedded_lyrics(audio_path):
                already_embedded += 1
                if verbose:
                    console.print(f"[cyan]– Already embedded:[/cyan] {file}")
                continue

            if lrc_path:
                success = embed_lyrics(audio_path, lrc_path, dry_run)
                if success:
                    embedded += 1
                    if not dry_run:
                        try:
                            os.remove(lrc_path)
                            lrc_deleted += 1
                        except Exception as e:
                            console.print(f"[red]Could not delete {lrc_path}: {e}[/red]")
                    if verbose:
                        console.print(f"[green]✓ Embedded lyrics into:[/green] {file}")
                else:
                    console.print(f"[red]✗ Failed to embed:[/red] {file}")
            elif verbose:
                console.print(f"[yellow]– No .lrc file found for:[/yellow] {file}")

        lyrics_folder = os.path.join(folder, "Lyrics")
        if os.path.isdir(lyrics_folder) and not os.listdir(lyrics_folder):
            try:
                if dry_run:
                    console.print(f"[yellow]Would delete empty Lyrics folder:[/yellow] {lyrics_folder}")
                else:
                    os.rmdir(lyrics_folder)
                    if verbose:
                        console.print(f"[green]Deleted empty Lyrics folder:[/green] {lyrics_folder}")
            except Exception as e:
                console.print(f"[red]Could not remove Lyrics folder: {lyrics_folder} — {e}[/red]")

    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Audio files scanned: {total}")
    console.print(f"Lyrics embedded: {embedded}")
    console.print(f"Already embedded: {already_embedded}")
    console.print(f".lrc files deleted: {lrc_deleted}")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")
    if total:
        console.print(f"Success rate: {embedded / total * 100:.2f}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed stripped .lrc lyrics into FLAC and MP3 files.")
    parser.add_argument("-d", "--directory", required=True, help="Root directory to scan")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without modifying files")
    parser.add_argument("--verbose", action="store_true", help="Print detailed output per file")
    args = parser.parse_args()
    scan_archive(args.directory, args.dry_run, args.verbose)