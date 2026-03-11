#!/usr/bin/env python3
"""
case_normalize.py - Enforce uniform lowercase naming for key archive files.
Renames things like 'Cover.JPG' → 'cover.jpg', 'Folder.JPEG' → 'cover.jpg'.
"""

from pathlib import Path
import argparse
from typing import List, Tuple

class CaseNormalizer:
    TARGET_NAMES = {
        "cover.jpg": {"cover.jpg", "cover.jpeg", "folder.jpg", "folder.jpeg",
                      "album cover.jpg", "album cover.jpeg", "albumartsmall.jpg"},
        "artist.jpg": {"artist.jpg", "folder.jpg"}  # for artist-level folders
    }

    def __init__(self, archive_root: Path):
        self.root = Path(archive_root)

    def check_file(self, file: Path) -> Tuple[bool, str]:
        """
        Check if file matches a target name (case-insensitive).
        Returns (needs_fix, suggested_name).
        """
        lower = file.name.lower()
        for target, variants in self.TARGET_NAMES.items():
            if lower in variants:
                if file.name != target:
                    return True, target
        return False, ""

    def scan_archive(self, dry_run: bool = True) -> dict:
        """
        Scan archive and optionally fix filenames.
        """
        results = {"fixed": [], "skipped": [], "clean": 0, "errors": []}

        for file in self.root.rglob("*"):
            if not file.is_file() or file.name.startswith("."):
                continue

            needs_fix, suggested = self.check_file(file)
            if needs_fix:
                dest = file.with_name(suggested)
                if dest.exists():
                    results["skipped"].append(str(file))
                    continue
                if dry_run:
                    results["fixed"].append(f"Would rename {file} → {dest}")
                else:
                    try:
                        file.rename(dest)
                        results["fixed"].append(f"Renamed {file} → {dest}")
                    except Exception as e:
                        results["errors"].append(f"Error renaming {file}: {e}")
            else:
                results["clean"] += 1

        return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize case of cover/artist files.")
    parser.add_argument("--archive", required=True, help="Archive root path")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without renaming")
    args = parser.parse_args()

    normalizer = CaseNormalizer(Path(args.archive))
    results = normalizer.scan_archive(dry_run=args.dry_run)

    print(f"\n🔍 Scanned: {args.archive}")
    print(f"✅ Clean files: {results['clean']}")
    print(f"🔄 Fixes: {len(results['fixed'])}")
    print(f"⏭️ Skipped (already exists): {len(results['skipped'])}")
    print(f"❌ Errors: {len(results['errors'])}\n")

    for line in results["fixed"][:10]:
        print(line)
    if len(results["fixed"]) > 10:
        print(f"... and {len(results['fixed']) - 10} more")