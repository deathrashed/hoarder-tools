#!/usr/bin/env python3
"""
Wrapper for Riley's Last.fm MP3 genre updater with hoarder-tools style dry-run support.
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
SCRIPT_PATH = Path("/Users/rd/Scripts/Riley/Audio/Genres/Lastfm/Genres from Lastfm.js")


def is_mp3_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".mp3"


def read_artist(audio_path: Path) -> str | None:
    try:
        audio = MutagenFile(audio_path)
        if not audio or not getattr(audio, "tags", None):
            return None
        value = audio.tags.get("TPE1") or audio.tags.get("artist")
        if not value:
            return None
        if isinstance(value, list):
            return str(value[0]).strip() or None
        if hasattr(value, "text") and value.text:
            return str(value.text[0]).strip() or None
        return str(value).strip() or None
    except Exception:
        return None


def collect_mp3_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.mp3") if path.is_file())


def build_artist_map(root: Path) -> tuple[list[Path], dict[str, list[Path]], list[Path]]:
    files = collect_mp3_files(root)
    artist_map: dict[str, list[Path]] = defaultdict(list)
    missing_artist = []

    for path in files:
        artist = read_artist(path)
        if artist:
            artist_map[artist].append(path)
        else:
            missing_artist.append(path)

    return files, artist_map, missing_artist


def validate_runtime() -> list[str]:
    problems = []
    if not SCRIPT_PATH.exists():
        problems.append(f"Missing external script: {SCRIPT_PATH}")
    if shutil.which("node") is None:
        problems.append("`node` is not available in PATH")
    if not os.environ.get("LASTFM_API_KEY"):
        problems.append("`LASTFM_API_KEY` is not set")
    return problems


def run_external(directory: Path) -> int:
    command = ["node", str(SCRIPT_PATH), str(directory)]
    return subprocess.run(command, check=False).returncode


def dry_run_report(root: Path, verbose: bool = False) -> int:
    files, artist_map, missing_artist = build_artist_map(root)

    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"MP3 files scanned: {len(files)}")
    console.print(f"Artists that would be queried: {len(artist_map)}")
    console.print(f"Files with missing artist tags: {len(missing_artist)}")
    console.print("Dry run: Yes")

    if verbose:
        if artist_map:
            console.print("\n[bold]Artists to update[/bold]")
            for artist in sorted(artist_map):
                console.print(f"- {artist} ({len(artist_map[artist])} file(s))")
        if missing_artist:
            console.print("\n[bold]Files missing artist tags[/bold]")
            for path in missing_artist:
                console.print(f"- {path}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Update MP3 genre tags from Last.fm artist tags.")
    parser.add_argument("-d", "--directory", required=True, help="Root directory to scan")
    parser.add_argument("--dry-run", action="store_true", help="Preview affected artists and files")
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
