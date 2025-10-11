#!/usr/bin/env python3
"""
track_gap_checker.py - Detect missing or inconsistent track numbers in album folders.
Now with --strict mode to flag albums not starting at 01 or with numbering resets.
"""

from pathlib import Path
import re
import argparse
from typing import List, Dict

class TrackGapChecker:
    TRACK_PATTERN = re.compile(r"^(\d{1,2})[.\-_\s]")  # e.g. "01.", "02 -", "03_"

    def __init__(self, archive_root: Path, strict: bool = False):
        self.root = Path(archive_root)
        self.strict = strict

    def extract_track_number(self, filename: str) -> int:
        match = self.TRACK_PATTERN.match(filename)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None

    def check_album_folder(self, folder: Path) -> Dict:
        tracks = []
        for f in folder.iterdir():
            if f.is_file() and not f.name.startswith("."):
                num = self.extract_track_number(f.name)
                if num is not None:
                    tracks.append(num)

        if not tracks:
            return {"folder": str(folder), "tracks": [], "missing": [], "strict_warnings": []}

        tracks = sorted(set(tracks))
        expected = list(range(tracks[0], tracks[-1] + 1))
        missing = [n for n in expected if n not in tracks]

        strict_warnings = []
        if self.strict:
            if tracks[0] != 1:
                strict_warnings.append(f"Does not start at 01 (starts at {tracks[0]:02d})")
            if tracks != sorted(tracks):
                strict_warnings.append("Track numbers out of order")
            # Detect large jumps (e.g. 01, 02, 07)
            for i in range(1, len(tracks)):
                if tracks[i] - tracks[i-1] > 2:
                    strict_warnings.append(f"Jump from {tracks[i-1]:02d} to {tracks[i]:02d}")

        return {"folder": str(folder), "tracks": tracks, "missing": missing, "strict_warnings": strict_warnings}

    def scan_archive(self) -> Dict:
        results = {
            "albums": [], 
            "albums_with_gaps": 0, 
            "clean": 0,
            "missing_tracks": [],
            "strict_issues": [],
            "total_albums": 0
        }

        for dirpath, _, filenames in self.root.walk():
            folder = Path(dirpath)
            if any(self.extract_track_number(f) for f in filenames):
                results["total_albums"] += 1
                report = self.check_album_folder(folder)
                if report["missing"] or report["strict_warnings"]:
                    results["albums"].append(report)
                    results["albums_with_gaps"] += 1
                    
                    # Categorize issues
                    if report["missing"]:
                        results["missing_tracks"].append(report)
                    if report["strict_warnings"]:
                        results["strict_issues"].append(report)
                else:
                    results["clean"] += 1

        return results


def print_report(results: Dict, archive_path: str, strict_mode: bool, output_file: str = None):
    """Print a comprehensive, readable report of album gap analysis."""
    
    # Prepare report content
    report_lines = []
    
    report_lines.append("=" * 80)
    report_lines.append("🎵 TRACK GAP ANALYSIS REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"📁 Archive: {archive_path}")
    report_lines.append(f"🔍 Mode: {'Strict' if strict_mode else 'Standard'}")
    report_lines.append(f"📊 Total Albums Scanned: {results['total_albums']}")
    report_lines.append("")
    
    # Summary Statistics
    report_lines.append("📈 SUMMARY STATISTICS")
    report_lines.append("-" * 40)
    report_lines.append(f"✅ Clean Albums: {results['clean']} ({results['clean']/max(1,results['total_albums'])*100:.1f}%)")
    report_lines.append(f"❌ Albums with Issues: {results['albums_with_gaps']} ({results['albums_with_gaps']/max(1,results['total_albums'])*100:.1f}%)")
    report_lines.append(f"🔢 Missing Tracks: {len(results['missing_tracks'])} albums")
    report_lines.append(f"⚠️  Strict Issues: {len(results['strict_issues'])} albums")
    report_lines.append("")
    
    if results['albums_with_gaps'] == 0:
        report_lines.append("🎉 All albums are clean! No gaps or issues found.")
    else:
        # Albums with Missing Tracks
        if results['missing_tracks']:
            report_lines.append("🔢 ALBUMS WITH MISSING TRACKS")
            report_lines.append("-" * 50)
            for i, album in enumerate(results['missing_tracks'], 1):
                folder_name = Path(album['folder']).name
                parent_name = Path(album['folder']).parent.name if Path(album['folder']).parent != Path(archive_path) else ""
                
                report_lines.append(f"{i:2d}. {folder_name}")
                if parent_name:
                    report_lines.append(f"    📁 Parent: {parent_name}")
                report_lines.append(f"    🎵 Found Tracks: {album['tracks']}")
                report_lines.append(f"    ❌ Missing: {album['missing']}")
                if album['strict_warnings']:
                    report_lines.append(f"    ⚠️  Additional Issues:")
                    for warn in album['strict_warnings']:
                        report_lines.append(f"        • {warn}")
                report_lines.append("")
        
        # Albums with Strict Mode Issues Only (no missing tracks)
        strict_only = [a for a in results['strict_issues'] if not a['missing']]
        if strict_only:
            report_lines.append("⚠️  ALBUMS WITH NUMBERING ISSUES (Strict Mode)")
            report_lines.append("-" * 55)
            for i, album in enumerate(strict_only, 1):
                folder_name = Path(album['folder']).name
                parent_name = Path(album['folder']).parent.name if Path(album['folder']).parent != Path(archive_path) else ""
                
                report_lines.append(f"{i:2d}. {folder_name}")
                if parent_name:
                    report_lines.append(f"    📁 Parent: {parent_name}")
                report_lines.append(f"    🎵 Found Tracks: {album['tracks']}")
                report_lines.append(f"    ⚠️  Issues:")
                for warn in album['strict_warnings']:
                    report_lines.append(f"        • {warn}")
                report_lines.append("")
        
        # Recommendations
        report_lines.append("💡 RECOMMENDATIONS")
        report_lines.append("-" * 30)
        if results['missing_tracks']:
            report_lines.append("• Check for missing audio files in the listed albums")
            report_lines.append("• Verify track numbering consistency")
            report_lines.append("• Consider re-downloading or re-ripping problematic albums")
        if results['strict_issues']:
            report_lines.append("• Standardize track numbering to start from 01")
            report_lines.append("• Ensure sequential numbering without gaps")
            report_lines.append("• Use consistent track number formatting")
        report_lines.append("")
    
    # Add timestamp
    from datetime import datetime
    report_lines.append("=" * 80)
    report_lines.append(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    
    # Output to console
    for line in report_lines:
        print(line)
    
    # Save to file if specified
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            print(f"\n📄 Report saved to: {output_file}")
        except Exception as e:
            print(f"\n❌ Error saving report to {output_file}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect missing track numbers in album folders.")
    parser.add_argument("--archive", required=True, help="Archive root path")
    parser.add_argument("--strict", action="store_true", help="Enable strict mode (start at 01, no jumps)")
    parser.add_argument("--summary-only", action="store_true", help="Show only summary statistics")
    parser.add_argument("--output", "-o", help="Output file path (default: missing_tracks.txt)")
    args = parser.parse_args()

    checker = TrackGapChecker(Path(args.archive), strict=args.strict)
    results = checker.scan_archive()

    if args.summary_only:
        print(f"📊 Summary: {results['clean']} clean, {results['albums_with_gaps']} with issues out of {results['total_albums']} total albums")
    else:
        # Default output file if not specified
        output_file = args.output or "missing_tracks.txt"
        print_report(results, args.archive, args.strict, output_file)