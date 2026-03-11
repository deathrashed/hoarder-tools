#!/usr/bin/env python3
"""
Flatten accidental split-track folders caused by slashes in track titles.
"""

import argparse
import os
import re
import shutil
from pathlib import Path

from mutagen import File as MutagenFile
from rich.console import Console
from rich.prompt import Confirm


console = Console()
AUDIO_EXTENSIONS = {".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wav", ".aif", ".aiff", ".alac"}
TRACK_FOLDER_PATTERN = re.compile(r"^\d{1,3}\.\s+")
TITLE_SEPARATOR = "／"


def is_audio_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS


def describe_folder(folder):
    parts = str(folder).strip(os.sep).split(os.sep)
    if len(parts) >= 3:
        return parts[-3], parts[-2], parts[-1]
    if len(parts) >= 2:
        return parts[-2], parts[-1], ""
    return "", parts[-1], ""


def read_track_title(audio_path: Path):
    try:
        audio = MutagenFile(audio_path)
        if not audio or not getattr(audio, "tags", None):
            return None

        for key in ("title", "TITLE"):
            value = audio.tags.get(key)
            if value:
                if isinstance(value, list):
                    return str(value[0]).strip()
                return str(value).strip()
    except Exception:
        return None
    return None


def sanitize_track_title(title: str) -> str:
    return " ".join(title.replace("/", TITLE_SEPARATOR).split()).strip()


def find_audio_files(folder: Path):
    return sorted(path for path in folder.rglob("*") if is_audio_file(path))


def normalize_fragment(fragment: str) -> str:
    return " ".join(fragment.split()).strip()


def should_append_with_separator(fragment: str) -> bool:
    return bool(fragment)


def build_fallback_title(split_folder: Path, audio_file: Path) -> str:
    folder_tail = split_folder.name.split(". ", 1)[1] if ". " in split_folder.name else split_folder.name
    title_parts = [normalize_fragment(folder_tail)]

    relative_parts = [normalize_fragment(part) for part in audio_file.relative_to(split_folder).parts[:-1] if normalize_fragment(part)]
    file_stem = normalize_fragment(audio_file.stem)

    if file_stem and not title_parts[0].lower().startswith(file_stem.lower()):
        relative_parts.append(file_stem)

    for fragment in relative_parts:
        cleaned_fragment = fragment.lstrip("_").strip()
        if not cleaned_fragment:
            continue
        if should_append_with_separator(fragment):
            title_parts.append(f"{TITLE_SEPARATOR}{cleaned_fragment}")
        else:
            title_parts.append(cleaned_fragment)

    return sanitize_track_title("".join(title_parts))


def build_fixed_filename(split_folder: Path, audio_file: Path) -> str:
    prefix = split_folder.name
    title = read_track_title(audio_file)
    if title:
        return f"{prefix.split('.', 1)[0]}. {sanitize_track_title(title)}{audio_file.suffix}"

    combined = build_fallback_title(split_folder, audio_file)
    track_number = prefix.split(".", 1)[0]
    return f"{track_number}. {combined}{audio_file.suffix}"


def is_candidate_split_folder(folder: Path) -> bool:
    if not TRACK_FOLDER_PATTERN.match(folder.name):
        return False

    try:
        items = list(folder.iterdir())
    except PermissionError:
        return False

    audio_files = find_audio_files(folder)
    return len(audio_files) == 1


def repair_split_track_folder(folder: Path, dry_run=False):
    audio_files = find_audio_files(folder)
    if len(audio_files) != 1:
        return {"status": "skipped", "reason": "expected exactly one audio file"}

    audio_file = audio_files[0]
    dest_name = build_fixed_filename(folder, audio_file)
    dest_path = folder.parent / dest_name

    if dest_path.exists():
        return {"status": "skipped", "reason": f"destination exists: {dest_path.name}"}

    if dry_run:
        return {"status": "fixed", "dest_path": str(dest_path), "dry_run": True}

    shutil.move(str(audio_file), str(dest_path))
    shutil.rmtree(folder)
    return {"status": "fixed", "dest_path": str(dest_path), "dry_run": False}


def collect_candidate_folders(root):
    candidates = []
    for dirpath, _, _ in os.walk(root):
        folder = Path(dirpath)
        if folder == Path(root):
            continue
        if is_candidate_split_folder(folder):
            candidates.append(folder)
    return candidates


def process_candidates(candidates, dry_run=False, verbose=False):
    fixed = 0
    skipped = 0

    for index, folder in enumerate(candidates, 1):
        letter, artist, album = describe_folder(folder)
        console.print(f"\n[{index}/{len(candidates)}] {letter} / {artist} / {album}", style="bold")
        result = repair_split_track_folder(folder, dry_run=dry_run)
        if result["status"] == "fixed":
            fixed += 1
            action = "Would move to" if result.get("dry_run") else "Moved to"
            console.print(f"[green]{action}[/green] {result['dest_path']}")
        else:
            skipped += 1
            if verbose:
                console.print(f"[yellow]Skipped:[/yellow] {result['reason']}")

    return {"candidate_count": len(candidates), "fixed": fixed, "skipped": skipped, "dry_run": dry_run}


def print_summary(summary):
    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Candidate folders scanned: {summary.get('candidate_count', 0)}")
    console.print(f"Folders repaired: {summary.get('fixed', 0)}")
    console.print(f"Folders skipped: {summary.get('skipped', 0)}")
    console.print(f"Dry run: {'Yes' if summary.get('dry_run', False) else 'No'}")


def maybe_apply_after_dry_run(candidates, should_prompt=False, verbose=False):
    if not should_prompt or not candidates:
        return False

    if not Confirm.ask("Apply these changes now?", default=False):
        return False

    console.print("\n[bold cyan]Applying changes...[/bold cyan]")
    summary = process_candidates(candidates, dry_run=False, verbose=verbose)
    print_summary(summary)
    return True


def scan_archive(root, dry_run=False, verbose=False):
    candidates = collect_candidate_folders(root)
    summary = process_candidates(candidates, dry_run=dry_run, verbose=verbose)
    print_summary(summary)
    return {"candidates": candidates, "summary": summary}


def main():
    parser = argparse.ArgumentParser(
        description="Fix accidental split-track folders caused by slashes in track titles."
    )
    parser.add_argument("-d", "--directory", required=True, help="Root directory to scan")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without moving files")
    parser.add_argument(
        "--prompt-apply-after-dry-run",
        action="store_true",
        help="Prompt to apply the same changes immediately after a dry run",
    )
    parser.add_argument("--verbose", action="store_true", help="Print skipped folders")
    args = parser.parse_args()

    result = scan_archive(args.directory, dry_run=args.dry_run, verbose=args.verbose)
    if args.dry_run:
        maybe_apply_after_dry_run(
            result["candidates"],
            should_prompt=args.prompt_apply_after_dry_run,
            verbose=args.verbose,
        )


if __name__ == "__main__":
    main()
