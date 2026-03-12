#!/usr/bin/env python3
"""
Wrapper for Riley's Discogs MP3 genre updater with hoarder-tools style dry-run support.
"""

import argparse
import os
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

from mutagen import File as MutagenFile
from rich.console import Console


console = Console()
SCRIPT_PATH = Path("/Users/rd/Scripts/Riley/Audio/Genres/Discogs/Genres from Discogs.js")


def is_mp3_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".mp3"


def read_artist_album(audio_path: Path) -> tuple[str | None, str | None]:
    try:
        audio = MutagenFile(audio_path)
        if not audio or not getattr(audio, "tags", None):
            return None, None

        def read_tag(*keys):
            for key in keys:
                value = audio.tags.get(key)
                if not value:
                    continue
                if isinstance(value, list):
                    return str(value[0]).strip() or None
                if hasattr(value, "text") and value.text:
                    return str(value.text[0]).strip() or None
                return str(value).strip() or None
            return None

        return read_tag("TPE1", "artist"), read_tag("TALB", "album")
    except Exception:
        return None, None


def collect_mp3_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.mp3") if path.is_file())


def build_album_map(root: Path) -> tuple[list[Path], dict[tuple[str, str], list[Path]], list[Path]]:
    files = collect_mp3_files(root)
    album_map: dict[tuple[str, str], list[Path]] = defaultdict(list)
    missing_tags = []

    for path in files:
        artist, album = read_artist_album(path)
        if artist and album:
            album_map[(artist, album)].append(path)
        else:
            missing_tags.append(path)

    return files, album_map, missing_tags


def validate_runtime() -> list[str]:
    problems = []
    if not SCRIPT_PATH.exists():
        problems.append(f"Missing external script: {SCRIPT_PATH}")
    if shutil.which("node") is None:
        problems.append("`node` is not available in PATH")
    if not os.environ.get("DISCOGS_API_TOKEN"):
        problems.append("`DISCOGS_API_TOKEN` is not set")
    return problems


def run_external(directory: Path) -> int:
    command = ["node", str(SCRIPT_PATH), str(directory)]
    return subprocess.run(command, check=False).returncode


def dry_run_report(root: Path, verbose: bool = False) -> int:
    files, album_map, missing_tags = build_album_map(root)

    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"MP3 files scanned: {len(files)}")
    console.print(f"Albums that would be queried: {len(album_map)}")
    console.print(f"Files with missing artist/album tags: {len(missing_tags)}")
    console.print("Dry run: Yes")

    if verbose:
        if album_map:
            console.print("\n[bold]Albums to update[/bold]")
            for artist, album in sorted(album_map):
                console.print(f"- {artist} / {album} ({len(album_map[(artist, album)])} file(s))")
        if missing_tags:
            console.print("\n[bold]Files missing artist/album tags[/bold]")
            for path in missing_tags:
                console.print(f"- {path}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Update MP3 genre tags and years from Discogs styles.")
    parser.add_argument("-d", "--directory", required=True, help="Root directory to scan")
    parser.add_argument("--dry-run", action="store_true", help="Preview affected albums and files")
    parser.add_argument("--verbose", action="store_true", help="Print detailed dry-run output")
    args = parser.parse_args()

    target = Path(args.directory).expanduser().resolve()
    if not target.is_dir():
        console.print(f"[red]Directory does not exist:[/red] {target}")
        return 1

    problems = validate_runtime()
    if problems:
        for problem in problems:
            console.print(f"[red]{problem}[/red]")
        return 1

    if args.dry_run:
        return dry_run_report(target, verbose=args.verbose)

    return run_external(target)


if __name__ == "__main__":
    raise SystemExit(main())
