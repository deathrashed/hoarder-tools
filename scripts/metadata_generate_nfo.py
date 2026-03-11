import os
import argparse
from mutagen.flac import FLAC
from mutagen.id3 import ID3, ID3NoHeaderError, USLT, APIC
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from rich.console import Console

console = Console()

def is_valid_audio(filename):
    return filename.lower().endswith((".flac", ".mp3")) and not filename.startswith("._")

def extract_metadata(audio_path):
    metadata = {
        "artist": "Unknown",
        "album": "Unknown",
        "year": "Unknown",
        "genre": "Unknown",
        "lyrics": False,
        "format": "FLAC" if audio_path.lower().endswith(".flac") else "MP3",
        "cover": "None"
    }

    try:
        if audio_path.lower().endswith(".flac"):
            audio = FLAC(audio_path)
            metadata.update({
                "artist": audio.get("artist", ["Unknown"])[0],
                "album": audio.get("album", ["Unknown"])[0],
                "year": audio.get("date", ["Unknown"])[0],
                "genre": audio.get("genre", ["Unknown"])[0],
                "lyrics": bool(audio.get("lyrics"))
            })
            for pic in audio.pictures:
                if pic.type == 3:
                    metadata["cover"] = f"{pic.width}x{pic.height} {pic.mime}"
                    break

        elif audio_path.lower().endswith(".mp3"):
            audio = MP3(audio_path, ID3=ID3)
            easy = EasyID3(audio_path)
            metadata.update({
                "artist": easy.get("artist", ["Unknown"])[0],
                "album": easy.get("album", ["Unknown"])[0],
                "year": easy.get("date", ["Unknown"])[0],
                "genre": easy.get("genre", ["Unknown"])[0],
                "lyrics": any(isinstance(tag, USLT) for tag in audio.tags.values())
            })
            for tag in audio.tags.values():
                if isinstance(tag, APIC) and tag.type == 3:
                    metadata["cover"] = f"{tag.desc or 'Embedded'} ({tag.mime})"
                    break

    except Exception as e:
        console.print(f"[red]❌ Error reading {audio_path}: {e}[/red]")

    return metadata

def write_album_nfo(folder, metadata, dry_run=False):
    path = os.path.join(folder, "album.nfo")
    if dry_run:
        console.print(f"[yellow]Would write album.nfo in {folder}[/yellow]")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Album: {metadata['album']} ({metadata['year']})\n")
        f.write(f"**Artist:** {metadata['artist']}\n")
        f.write(f"**Genre:** {metadata['genre']}\n")
        f.write(f"**Format:** {metadata['format']}\n")
        f.write(f"**Cover:** {metadata['cover']}\n")
        f.write(f"**Lyrics:** {'✅' if metadata['lyrics'] else '❌'}\n")

def write_artist_nfo(folder, metadata, dry_run=False):
    path = os.path.join(folder, "artist.nfo")
    if dry_run:
        console.print(f"[yellow]Would write artist.nfo in {folder}[/yellow]")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Artist: {metadata['artist']}\n")
        f.write(f"**Genre:** {metadata['genre']}\n")
        f.write(f"**Origin:** Unknown\n")
        f.write(f"**Years Active:** Unknown\n")
        f.write(f"**MusicBrainz ID:** Unknown\n")
        f.write("\n### Biography:\nThis artist.nfo was generated from embedded metadata. Web enrichment coming soon.\n")

def process_album_folder(folder, dry_run=False, verbose=False):
    for filename in sorted(os.listdir(folder)):
        if is_valid_audio(filename):
            audio_path = os.path.join(folder, filename)
            metadata = extract_metadata(audio_path)
            write_album_nfo(folder, metadata, dry_run)
            write_artist_nfo(folder, metadata, dry_run)
            if verbose:
                console.print(f"[green]📝 Generated .nfo files for:[/green] {folder}")
            return True
    return False

def scan_archive(root_path, dry_run=False, verbose=False):
    processed = 0
    for dirpath, _, filenames in os.walk(root_path):
        if any(is_valid_audio(f) for f in filenames):
            if process_album_folder(dirpath, dry_run, verbose):
                processed += 1

    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Album folders processed: {processed}")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate album.nfo and artist.nfo from embedded metadata.")
    parser.add_argument("-d", "--directory", required=True, help="Root directory to scan")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without writing files")
    parser.add_argument("--verbose", action="store_true", help="Print detailed output per folder")
    args = parser.parse_args()
    scan_archive(args.directory, args.dry_run, args.verbose)