#!/usr/bin/env python3
"""
Queue tracks with missing lyrics in the Lyrics Finder app.
"""

import argparse
import os
import subprocess

from rich.console import Console

from lyrics_embed_from_lrc import AUDIO_EXTS, find_lrc, has_embedded_lyrics


console = Console()


def is_audio_file(filename):
    return filename.lower().endswith(tuple(AUDIO_EXTS))


def collect_missing_lyrics_tracks(root, include_sidecar_lrc=False):
    """Return audio tracks that do not have embedded lyrics."""
    matches = []

    for dirpath, _, filenames in os.walk(root):
        for filename in sorted(filenames):
            if not is_audio_file(filename):
                continue

            audio_path = os.path.join(dirpath, filename)
            if has_embedded_lyrics(audio_path):
                continue

            if not include_sidecar_lrc and find_lrc(audio_path):
                continue

            matches.append(audio_path)

    return matches


def load_track_list(path):
    with open(path, "r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def open_in_lyrics_finder(paths):
    subprocess.run(["/usr/bin/open", "-a", "Lyrics Finder", *paths], check=True)


def main():
    parser = argparse.ArgumentParser(
        description="Open tracks with missing embedded lyrics in Lyrics Finder."
    )
    parser.add_argument("-d", "--directory", help="Root directory to scan")
    parser.add_argument(
        "--path-list",
        help="Newline-delimited file containing track paths to open in Lyrics Finder",
    )
    parser.add_argument(
        "--include-sidecar-lrc",
        action="store_true",
        help="Also queue tracks that already have a matching .lrc file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show tracks that would be queued without opening Lyrics Finder",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each queued track path",
    )
    args = parser.parse_args()

    if args.path_list:
        tracks = load_track_list(args.path_list)
    elif args.directory:
        tracks = collect_missing_lyrics_tracks(
            args.directory, include_sidecar_lrc=args.include_sidecar_lrc
        )
    else:
        parser.error("either --directory or --path-list is required")

    if not tracks:
        console.print("[yellow]No tracks need Lyrics Finder[/yellow]")
        return

    console.print(f"[bold]Tracks to queue in Lyrics Finder:[/bold] {len(tracks)}")
    if args.verbose or args.dry_run:
        for track in tracks:
            console.print(track)

    if args.dry_run:
        return

    try:
        open_in_lyrics_finder(tracks)
        console.print(f"[green]Opened {len(tracks)} track(s) in Lyrics Finder[/green]")
    except subprocess.CalledProcessError as exc:
        console.print(f"[red]Failed to open Lyrics Finder: {exc}[/red]")
        raise SystemExit(exc.returncode) from exc


if __name__ == "__main__":
    main()
