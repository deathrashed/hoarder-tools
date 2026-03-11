#!/usr/bin/env python3
"""
Find audio tracks that do not have embedded lyrics and write them to a path list.
"""

import argparse
import os

from rich.console import Console
from rich.prompt import Confirm

from lyrics_embed_from_lrc import AUDIO_EXTS, has_embedded_lyrics
from lyrics_send_to_lyrics_finder import load_track_list, open_in_lyrics_finder


console = Console()


def is_audio_file(filename):
    return filename.lower().endswith(tuple(AUDIO_EXTS))


def describe_folder(folder):
    parts = folder.strip(os.sep).split(os.sep)
    if len(parts) >= 3:
        return parts[-3], parts[-2], parts[-1]
    if len(parts) >= 2:
        return parts[-2], parts[-1], ""
    return "", parts[-1], ""


def scan_archive_for_missing_embedded_lyrics(root, verbose=False):
    matches = []
    folders = []
    total_audio_files = 0

    for dirpath, _, filenames in os.walk(root):
        if any(is_audio_file(filename) for filename in filenames):
            folders.append(dirpath)

    for index, folder in enumerate(folders, 1):
        letter, artist, album = describe_folder(folder)
        console.print(f"\n[{index}/{len(folders)}] {letter} / {artist} / {album}", style="bold")

        for filename in sorted(os.listdir(folder)):
            if not is_audio_file(filename):
                continue

            total_audio_files += 1
            audio_path = os.path.join(folder, filename)
            if not has_embedded_lyrics(audio_path):
                matches.append(audio_path)
                if verbose:
                    console.print(f"[yellow]– Missing embedded lyrics:[/yellow] {filename}")
            elif verbose:
                console.print(f"[cyan]– Already embedded:[/cyan] {filename}")

    return {
        "matches": matches,
        "folders_scanned": len(folders),
        "total_audio_files": total_audio_files,
        "missing_embedded_lyrics": len(matches),
    }


def collect_tracks_missing_embedded_lyrics(root):
    return scan_archive_for_missing_embedded_lyrics(root)["matches"]


def write_track_list(paths, output_path):
    with open(output_path, "w", encoding="utf-8") as handle:
        for path in paths:
            handle.write(f"{path}\n")


def open_track_list_in_lyrics_finder(path_list):
    open_in_lyrics_finder(load_track_list(path_list))


def maybe_open_track_list(path_list, should_open=False):
    if should_open:
        open_track_list_in_lyrics_finder(path_list)


def maybe_prompt_open_track_list(path_list, should_prompt=False):
    if not should_prompt:
        return

    if Confirm.ask("Open the saved path list in Lyrics Finder now?", default=False):
        open_track_list_in_lyrics_finder(path_list)


def print_summary(report, output_path):
    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Folders scanned: {report['folders_scanned']}")
    console.print(f"Audio files scanned: {report['total_audio_files']}")
    console.print(f"Tracks missing embedded lyrics: {report['missing_embedded_lyrics']}")
    console.print(f"Path list written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Write a list of tracks that are missing embedded lyrics."
    )
    parser.add_argument("-d", "--directory", required=True, help="Root directory to scan")
    parser.add_argument(
        "-o",
        "--output",
        default="missing_embedded_lyrics.txt",
        help="Output file for newline-delimited track paths",
    )
    parser.add_argument("--verbose", action="store_true", help="Print each matching track")
    parser.add_argument(
        "--open-in-lyrics-finder",
        action="store_true",
        help="After writing the file list, open that list in Lyrics Finder",
    )
    parser.add_argument(
        "--prompt-open-in-lyrics-finder",
        action="store_true",
        help="After writing the file list, prompt to open that list in Lyrics Finder",
    )
    args = parser.parse_args()

    report = scan_archive_for_missing_embedded_lyrics(args.directory, verbose=args.verbose)
    write_track_list(report["matches"], args.output)
    print_summary(report, args.output)

    maybe_open_track_list(args.output, should_open=args.open_in_lyrics_finder)
    if args.open_in_lyrics_finder:
        console.print("[green]Sent file list to Lyrics Finder[/green]")
    maybe_prompt_open_track_list(args.output, should_prompt=args.prompt_open_in_lyrics_finder)


if __name__ == "__main__":
    main()
