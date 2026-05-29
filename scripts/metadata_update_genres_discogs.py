#!/usr/bin/env python3
"""
Wrapper for Riley's Discogs MP3 genre updater with hoarder-tools style dry-run support.

Purpose: Update MP3 genre tags and years from Discogs styles
Usage: python metadata_update_genres_discogs.py -d /path/to/albums [--dry-run]
Options:
  --dry-run    Preview affected albums without making changes
  --verbose    Print detailed dry-run output
Exit codes:
  0 - Success or dry-run completed
  1 - Error (missing deps, invalid directory, etc.)
Config keys used: audio.library (fallback paths)
Env keys used: DISCOGS_API_TOKEN (via get_api_key)
"""

import argparse
import os
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# Add shared config module from ~/.config/tools/
CONFIG_TOOLS = str(Path.home() / ".config" / "tools")
if CONFIG_TOOLS not in sys.path:
    sys.path.insert(0, CONFIG_TOOLS)

try:
    from config import load_config, get_api_key, get_audio_library, get_path
except ImportError:

    def load_config():
        return {}

    def get_api_key(k, c=None):
        return os.environ.get(k)

    def get_audio_library(c):
        return None

    def get_path(c, k, d=None):
        return d


from mutagen import File as MutagenFile
from rich.console import Console

console = Console()

# Load config for fallback paths and external script location
_CONFIG = load_config()
EXTERNAL_SCRIPT_DEFAULT = (
    Path.home()
    / "Scripts"
    / "Riley"
    / "Audio"
    / "Genres"
    / "Discogs"
    / "Genres from Discogs.js"
)


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


def build_album_map(
    root: Path,
) -> tuple[list[Path], dict[tuple[str, str], list[Path]], list[Path]]:
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


def get_external_script_path() -> Path:
    """Get external script path from config or default."""
    script_path = get_path(_CONFIG, "external_scripts.discogs_genres")
    if script_path:
        return Path(script_path)
    return EXTERNAL_SCRIPT_DEFAULT


def validate_runtime() -> list[str]:
    problems = []
    script_path = get_external_script_path()
    if not script_path.exists():
        problems.append(f"Missing external script: {script_path}")
    if shutil.which("node") is None:
        problems.append("`node` is not available in PATH")
    if not get_api_key("DISCOGS_API_TOKEN", _CONFIG):
        problems.append("`DISCOGS_API_TOKEN` is not set (in .env or environment)")
    return problems


def run_external(directory: Path) -> int:
    script_path = get_external_script_path()
    api_token = get_api_key("DISCOGS_API_TOKEN", _CONFIG)
    env = os.environ.copy()
    env["DISCOGS_API_TOKEN"] = api_token or ""
    command = ["node", str(script_path), str(directory)]
    return subprocess.run(command, check=False, env=env).returncode


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
                console.print(
                    f"- {artist} / {album} ({len(album_map[(artist, album)])} file(s))"
                )
        if missing_tags:
            console.print("\n[bold]Files missing artist/album tags[/bold]")
            for path in missing_tags:
                console.print(f"- {path}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update MP3 genre tags and years from Discogs styles."
    )
    parser.add_argument(
        "-d", "--directory", required=True, help="Root directory to scan"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview affected albums and files"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print detailed dry-run output"
    )
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

