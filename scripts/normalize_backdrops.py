#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
from collections import defaultdict
from pathlib import Path

from rich.console import Console


PATTERN = re.compile(r"^backdrop(?:([1-9][0-9]*))?\.jpg$")
console = Console()


def sort_key(path: Path) -> tuple[int, str]:
    match = PATTERN.match(path.name)
    assert match is not None
    index = 0 if match.group(1) is None else int(match.group(1))
    return (index, path.name)


def desired_name(position: int) -> str:
    return "backdrop.jpg" if position == 0 else f"backdrop{position}.jpg"


def collect(root: Path) -> dict[Path, list[Path]]:
    folders: dict[Path, list[Path]] = defaultdict(list)
    for path in root.rglob("*"):
        if path.is_file() and PATTERN.match(path.name):
            folders[path.parent].append(path)
    return folders


def plan_for_folder(folder: Path, files: list[Path]) -> list[tuple[Path, Path]]:
    ordered = sorted(files, key=sort_key)
    plan: list[tuple[Path, Path]] = []
    for position, source in enumerate(ordered):
        target = folder / desired_name(position)
        if source != target:
            plan.append((source, target))
    return plan


def execute_plan(plan: list[tuple[Path, Path]]) -> None:
    staged: list[tuple[Path, Path]] = []
    for index, (source, target) in enumerate(plan):
        temp = source.with_name(f".{source.name}.codex-tmp-{index}")
        source.rename(temp)
        staged.append((temp, target))
    for temp, target in staged:
        temp.rename(target)


def describe_folder(folder: Path) -> tuple[str, str, str]:
    parts = str(folder).strip(os.sep).split(os.sep)
    if len(parts) >= 3:
        return parts[-3], parts[-2], parts[-1]
    if len(parts) >= 2:
        return parts[-2], parts[-1], ""
    return "", parts[-1], ""


def scan_archive(root: Path, dry_run: bool = False, verbose: bool = False) -> dict[str, int]:
    folders = collect(root)
    all_plans: list[tuple[Path, list[tuple[Path, Path]]]] = []

    for folder in sorted(folders):
        plan = plan_for_folder(folder, folders[folder])
        if plan:
            all_plans.append((folder, plan))

    folder_count = len(all_plans)
    rename_count = 0

    for index, (folder, plan) in enumerate(all_plans, 1):
        letter, artist, album = describe_folder(folder)
        console.print(f"\n[{index}/{folder_count}] {letter} / {artist} / {album}", style="bold")
        for source, target in plan:
            rename_count += 1
            action = "Would rename" if dry_run else "Renamed"
            console.print(f"[yellow]{action}[/yellow] {source.name} -> {target.name}" if dry_run else f"[green]{action}[/green] {source.name} -> {target.name}")
        if not dry_run:
            execute_plan(plan)
        elif verbose and not plan:
            console.print("[cyan]No changes needed[/cyan]")

    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Folders to change: {folder_count}")
    console.print(f"Files to rename: {rename_count}")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")

    return {"folders_to_change": folder_count, "files_to_rename": rename_count}


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize backdrop image names into a sequential series.")
    parser.add_argument("-d", "--directory", default=".", help="Root directory to scan")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without renaming files")
    parser.add_argument("--verbose", action="store_true", help="Reserved for future verbose output")
    args = parser.parse_args()

    root = Path(args.directory).resolve()
    scan_archive(root, dry_run=args.dry_run, verbose=args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
