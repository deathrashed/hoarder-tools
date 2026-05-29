import os
import argparse
import subprocess
from rich.console import Console

console = Console()

# Default lossy formats to archive
LOSSY_EXTS = {".mp3", ".aac", ".ogg", ".m4a", ".wav"}

def find_matching_lossy(folder, exts):
    """Return lossy files that have a matching FLAC in the same folder."""
    flac_files = {os.path.splitext(f)[0] for f in os.listdir(folder) if f.lower().endswith(".flac")}
    if not flac_files:
        return []  # Skip folders with no FLACs
    return [f for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in exts and os.path.splitext(f)[0] in flac_files]

def get_archive_command_and_extension(archive_type):
    """Return the command and file extension for the specified archive type."""
    commands = {
        "7z": (["7zz", "a"], ".7z"),
        "zip": (["7zz", "a"], ".zip"),
        "tar.gz": (["tar", "-czf"], ".tar.gz"),
        "tar.xz": (["tar", "-cJf"], ".tar.xz"),
        "tar.bz2": (["tar", "-cjf"], ".tar.bz2"),
        "xz": (["xz", "-z"], ".xz"),
        "gzip": (["gzip"], ".gz"),
        "bzip2": (["bzip2"], ".bz2")
    }
    return commands.get(archive_type.lower(), (["7zz", "a"], ".7z"))

def get_archive_contents(archive_path, exts):
    """List lossy files already inside an existing archive."""
    try:
        # Determine archive type and use appropriate command
        if archive_path.lower().endswith(('.tar.gz', '.tar.xz', '.tar.bz2')):
            result = subprocess.run(["tar", "-tf", archive_path], capture_output=True, text=True)
        elif archive_path.lower().endswith('.tar'):
            result = subprocess.run(["tar", "-tf", archive_path], capture_output=True, text=True)
        else:
            # Default to 7zz for 7z, zip, and other formats
            result = subprocess.run(["7zz", "l", archive_path], capture_output=True, text=True)
        
        lines = result.stdout.splitlines()
        files = []
        for line in lines:
            if archive_path.lower().endswith(('.tar.gz', '.tar.xz', '.tar.bz2', '.tar')):
                # Tar format - line is just the filename
                filename = line.strip()
                if os.path.splitext(filename.lower())[1] in exts:
                    files.append(os.path.basename(filename))
            else:
                # 7zz format - need to parse output
                parts = line.strip().split()
                if len(parts) > 3 and os.path.splitext(parts[-1].lower())[1] in exts:
                    files.append(os.path.basename(parts[-1]))
        return set(files)
    except Exception as e:
        console.print(f"[red]Could not read archive: {archive_path} — {e}[/red]")
        return set()

def archive_and_delete(folder, lossy_files, exts, archive_type="7z", dry_run=False, verbose=False, keep=False):
    """Archive lossy files into specified format and delete originals unless --keep is set."""
    archive_ext = get_archive_command_and_extension(archive_type)[1]
    archive_base = f"Lossy{archive_ext}"
    
    archive_file = None
    for f in os.listdir(folder):
        if f.startswith("MP3.") or f.startswith("Lossy."):
            if not os.path.splitext(f)[1].lower() in exts:
                archive_file = os.path.join(folder, f)
                break

    # If an archive already exists, skip files already inside
    if archive_file:
        archived_files = get_archive_contents(archive_file, exts)
        to_delete = [f for f in lossy_files if f in archived_files]
        for f in to_delete:
            if dry_run or keep:
                console.print(f"[yellow]Would delete already-archived:[/yellow] {f}")
            else:
                os.remove(os.path.join(folder, f))
                if verbose:
                    console.print(f"[green]Deleted already-archived:[/green] {f}")
        lossy_files = [f for f in lossy_files if f not in archived_files]

    if lossy_files:
        archive_path = os.path.join(folder, archive_base)
        if dry_run:
            console.print(f"[yellow]Would archive {len(lossy_files)} files into {archive_path}[/yellow]")
            return 0
        try:
            cmd, _ = get_archive_command_and_extension(archive_type)
            
            if archive_type.lower() in ["tar.gz", "tar.xz", "tar.bz2"]:
                # For tar formats, we need to create the archive with all files at once
                subprocess.run(cmd + [archive_path] + lossy_files, cwd=folder, check=True)
            elif archive_type.lower() in ["xz", "gzip", "bzip2"]:
                # For single-file compressors, we need to create a tar first, then compress
                temp_tar = os.path.join(folder, "temp.tar")
                subprocess.run(["tar", "-cf", temp_tar] + lossy_files, cwd=folder, check=True)
                subprocess.run(cmd + [temp_tar], cwd=folder, check=True)
                # Rename the compressed file
                compressed_file = temp_tar + archive_ext
                if os.path.exists(compressed_file):
                    os.rename(compressed_file, archive_path)
                if os.path.exists(temp_tar):
                    os.remove(temp_tar)
            else:
                # For 7z and zip formats
                subprocess.run(cmd + [archive_path] + lossy_files, cwd=folder, check=True)
            
            if keep:
                console.print(f"[cyan]{len(lossy_files)} files archived (kept originals) in:[/cyan] {folder}")
            else:
                for f in lossy_files:
                    os.remove(os.path.join(folder, f))
                    if verbose:
                        console.print(f"[green]Archived and deleted:[/green] {f}")
                console.print(f"[cyan]{len(lossy_files)} files archived and deleted in:[/cyan] {folder}")
            return len(lossy_files)
        except Exception as e:
            console.print(f"[red]Error archiving in {folder}: {e}[/red]")
            return 0
    return 0

def scan_archive(root, exts, archive_type="7z", dry_run=False, verbose=False, keep=False):
    total_archived = 0
    folders = []

    for dirpath, _, _ in os.walk(root):
        lossy = find_matching_lossy(dirpath, exts)
        if lossy:
            folders.append((dirpath, lossy))

    for index, (folder, lossy) in enumerate(folders, 1):
        console.print(f"\n[{index}/{len(folders)}] {folder}", style="bold")
        archived = archive_and_delete(folder, lossy, exts, archive_type, dry_run, verbose, keep)
        total_archived += archived

    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Folders scanned: {len(folders)}")
    console.print(f"Lossy files archived: {total_archived}")
    console.print(f"Archive format: {archive_type}")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")
    console.print(f"Keep originals: {'Yes' if keep else 'No'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Archive lossy files (MP3, AAC, OGG, etc.) that duplicate FLACs into various archive formats and optionally delete originals.")
    parser.add_argument("-d", "--directory", required=True, help="Root directory to scan")
    parser.add_argument("--ext", nargs="+", default=list(LOSSY_EXTS), help="Lossy extensions to archive (default: mp3, aac, ogg, m4a, wav)")
    parser.add_argument("--format", default="7z", choices=["7z", "zip", "tar.gz", "tar.xz", "tar.bz2", "xz", "gzip", "bzip2"], 
                       help="Archive format (default: 7z)")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without modifying files")
    parser.add_argument("--verbose", action="store_true", help="Print detailed output per file")
    parser.add_argument("--keep", action="store_true", help="Archive but keep originals instead of deleting")
    args = parser.parse_args()
    scan_archive(args.directory, set(ext.lower() for ext in args.ext), args.format, args.dry_run, args.verbose, args.keep)