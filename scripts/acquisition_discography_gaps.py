#!/usr/bin/env python3
"""
Find missing releases in an artist discography and optionally send them to deemon.
"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import time
import re
from pathlib import Path

import requests
from rich.console import Console
from rich.prompt import Prompt


console = Console()
COLLECTION_MATCHER_PATH = Path("/Users/rd/Scripts/Riley/DeemixKit/scripts/rileys-collection-matcher.py")
DEEZER_SEARCH_ALBUM_URL = "https://api.deezer.com/search/album"
DEEZER_ARTIST_ALBUMS_URL = "https://api.deezer.com/artist/{artist_id}/albums"
DEEZER_ALBUM_BASE = "https://www.deezer.com/album/"


def resolve_matcher_collection_path(collection_path: Path) -> Path:
    resolved = collection_path.expanduser().resolve()
    for candidate in [resolved, *resolved.parents]:
        if candidate.name == "Audio":
            return candidate
    return resolved


def load_collection_matcher():
    if not COLLECTION_MATCHER_PATH.exists():
        raise FileNotFoundError(f"Collection matcher not found: {COLLECTION_MATCHER_PATH}")
    spec = importlib.util.spec_from_file_location("riley_collection_matcher", COLLECTION_MATCHER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load collection matcher: {COLLECTION_MATCHER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CollectionMatcher


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "hoarder-tools/1.0"})
    return session


def search_reference_album(session: requests.Session, band: str, album: str) -> dict:
    response = session.get(DEEZER_SEARCH_ALBUM_URL, params={"q": f"{band} {album}", "limit": 20}, timeout=10)
    response.raise_for_status()
    data = response.json()
    albums = data.get("data") or []
    if not albums:
        raise ValueError(f"No album found for: {band} - {album}")
    return albums[0]


def fetch_artist_discography(session: requests.Session, artist_id: int) -> list[dict]:
    albums = []
    url = DEEZER_ARTIST_ALBUMS_URL.format(artist_id=artist_id)
    while url:
        response = session.get(url, params={"limit": 100}, timeout=10)
        response.raise_for_status()
        data = response.json()
        albums.extend(data.get("data") or [])
        url = data.get("next")
        if url:
            time.sleep(0.3)
    return albums


def filter_discography(albums: list[dict], include_singles: bool = False) -> list[dict]:
    if include_singles:
        filtered = albums
    else:
        filtered = [album for album in albums if (album.get("record_type") or "").lower() in {"album", "ep"}]

    seen_titles = set()
    unique = []
    for album in filtered:
        title = (album.get("title") or "").strip().lower()
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        unique.append(album)
    return unique


def build_release_entries(albums: list[dict], artist_name: str) -> list[dict]:
    entries = []
    for album in albums:
        album_id = album.get("id")
        if not album_id:
            continue
        entries.append(
            {
                "artist": artist_name,
                "album": album.get("title", "").strip(),
                "year": str(album.get("release_date", "")).split("-", 1)[0],
                "record_type": album.get("record_type", ""),
                "deezer_url": f"{DEEZER_ALBUM_BASE}{album_id}",
            }
        )
    return entries


def split_missing_releases(releases: list[dict], matcher) -> tuple[list[dict], list[dict]]:
    missing = []
    existing = []
    for release in releases:
        if matcher.is_album_in_collection(release["artist"], release["album"], release["year"]):
            existing.append(release)
        else:
            missing.append(release)
    return missing, existing


def write_url_list(releases: list[dict], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8") as handle:
        for release in releases:
            handle.write(f"{release['deezer_url']}\n")


def resolve_deemon_command() -> list[str] | None:
    deemon_path = shutil.which("deemon")
    if deemon_path:
        return [deemon_path]
    return None


def download_with_deemon(releases: list[dict]) -> int:
    deemon_command = resolve_deemon_command()
    if deemon_command is None:
        console.print("[red]`deemon` is not available in PATH[/red]")
        return 1

    command = [*deemon_command, "download"]
    for release in releases:
        command.extend(["--url", release["deezer_url"]])

    console.print(f"[cyan]Running:[/cyan] {' '.join(command)}")
    return subprocess.run(command, check=False).returncode


def print_release_list(title: str, releases: list[dict], numbered: bool = False) -> None:
    if not releases:
        return
    console.print(f"\n[bold]{title}[/bold]")
    for index, release in enumerate(releases, 1):
        record_type = release["record_type"] or "unknown"
        prefix = f"{index}. " if numbered else "- "
        console.print(f"{prefix}{release['artist']} / {release['album']} [{record_type}]")


def parse_release_selection(selection: str, total: int) -> list[int]:
    indexes = set()
    for token in re.split(r"[\s,]+", selection.strip()):
        if not token:
            continue
        if token.isdigit():
            index = int(token)
            if 1 <= index <= total:
                indexes.add(index)
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            if start_text.isdigit() and end_text.isdigit():
                start = int(start_text)
                end = int(end_text)
                if start > end:
                    start, end = end, start
                for index in range(start, end + 1):
                    if 1 <= index <= total:
                        indexes.add(index)
    return sorted(indexes)


def select_releases_by_numbers(releases: list[dict], numbers: list[int]) -> list[dict]:
    selected = []
    seen = set()
    for number in sorted(numbers):
        if 1 <= number <= len(releases) and number not in seen:
            selected.append(releases[number - 1])
            seen.add(number)
    return selected


def prompt_for_release_subset(releases: list[dict]) -> list[dict]:
    if not releases:
        return releases

    selection = Prompt.ask(
        "Enter release numbers to download (blank to skip, supports spaces, commas, or ranges like 1-3)",
        default="",
    ).strip()

    if not selection:
        return []

    numbers = parse_release_selection(selection, len(releases))
    if not numbers:
        console.print("[yellow]No valid release numbers selected. Skipping download.[/yellow]")
        return []

    chosen = select_releases_by_numbers(releases, numbers)
    console.print(f"Selected {len(chosen)} of {len(releases)} missing releases for download.")
    return chosen


def run_workflow(
    collection_path: Path,
    band: str,
    album: str,
    include_singles: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    output: Path | None = None,
    download_missing: bool = False,
) -> int:
    matcher_root = resolve_matcher_collection_path(collection_path)
    matcher_class = load_collection_matcher()
    matcher = matcher_class(str(matcher_root))
    session = create_session()

    if matcher_root != collection_path:
        console.print(f"Using collection root for matching: {matcher_root}")

    found_album = search_reference_album(session, band, album)
    artist = found_album.get("artist") or {}
    artist_id = artist.get("id")
    artist_name = artist.get("name") or band
    if not artist_id:
        raise ValueError("Could not resolve artist ID from Deezer")

    discography = fetch_artist_discography(session, int(artist_id))
    filtered = filter_discography(discography, include_singles=include_singles)
    releases = build_release_entries(filtered, artist_name)
    missing, existing = split_missing_releases(releases, matcher)

    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Artist resolved: {artist_name}")
    console.print(f"Releases found: {len(releases)}")
    console.print(f"Missing releases: {len(missing)}")
    console.print(f"Existing releases: {len(existing)}")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")

    if verbose or (download_missing and not dry_run and missing):
        print_release_list("Missing Releases", missing, numbered=download_missing and not dry_run)
    if verbose:
        print_release_list("Existing Releases", existing)

    if dry_run or not download_missing or not missing:
        if output:
            write_url_list(missing, output)
            console.print(f"Missing release URLs written to: {output}")
        return 0

    selected_missing = prompt_for_release_subset(missing)

    if output:
        write_url_list(selected_missing, output)
        console.print(f"Missing release URLs written to: {output}")

    if not selected_missing:
        console.print("[yellow]No releases selected for download.[/yellow]")
        return 0

    return download_with_deemon(selected_missing)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare a Deezer discography against your collection and optionally download missing releases."
    )
    parser.add_argument("-d", "--directory", required=True, help="Collection root to compare against")
    parser.add_argument("--band", required=True, help="Band or artist name")
    parser.add_argument("--album", required=True, help="Known album used to identify the correct artist")
    parser.add_argument("--include-singles", action="store_true", help="Include singles in discography results")
    parser.add_argument("--dry-run", action="store_true", help="Preview missing releases without downloading")
    parser.add_argument("--verbose", action="store_true", help="Print missing and existing release lists")
    parser.add_argument("-o", "--output", help="Optional file to write missing Deezer album URLs")
    parser.add_argument(
        "--download-with-deemon",
        action="store_true",
        help="Queue missing releases through deemon on real runs",
    )
    args = parser.parse_args()

    try:
        return run_workflow(
            collection_path=Path(args.directory).expanduser().resolve(),
            band=args.band,
            album=args.album,
            include_singles=args.include_singles,
            dry_run=args.dry_run,
            verbose=args.verbose,
            output=Path(args.output).expanduser().resolve() if args.output else None,
            download_missing=args.download_with_deemon,
        )
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
