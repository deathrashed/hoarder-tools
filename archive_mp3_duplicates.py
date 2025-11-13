import os
import argparse
import subprocess
from rich.console import Console

console = Console()

def find_matching_mp3s(folder):
    """Return MP3s that have a matching FLAC in the same folder."""
    flac_files = {os.path.splitext(f)[0] for f in os.listdir(folder) if f.lower().endswith(".flac")}
    if not flac_files:
        return []  # Skip folders with no FLACs
    return [f for f in os.listdir(folder) if f.lower().endswith(".mp3") and os.path.splitext(f)[0] in flac_files]

def get_archive_contents(archive_path):
    """List MP3s already inside an existing archive."""
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
                if line.strip().lower().endswith(".mp3"):
                    files.append(os.path.basename(line.strip()))
            else:
                # 7zz format - need to parse output
                parts = line.strip().split()
                if len(parts) > 3 and parts[-1].lower().endswith(".mp3"):
                    files.append(os.path.basename(parts[-1]))
        return set(files)
    except Exception as e:
        console.print(f"[red]Could not read archive: {archive_path} — {e}[/red]")
        return set()

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

def archive_and_delete(folder, mp3_files, archive_type="7z", dry_run=False, verbose=False, keep=False):
    """Archive MP3s into specified format and delete originals unless --keep is set."""
    archive_ext = get_archive_command_and_extension(archive_type)[1]
    archive_base = f"MP3{archive_ext}"
    
    archive_file = None
    for f in os.listdir(folder):
        if f.startswith("MP3.") and not f.lower().endswith(".mp3"):
            archive_file = os.path.join(folder, f)
            break

    # If an archive already exists, skip files already inside
    if archive_file:
        archived_files = get_archive_contents(archive_file)
        to_delete = [f for f in mp3_files if f in archived_files]
        for f in to_delete:
            if dry_run or keep:
                console.print(f"[yellow]Would delete already-archived:[/yellow] {f}")
            else:
                os.remove(os.path.join(folder, f))
                if verbose:
                    console.print(f"[green]Deleted already-archived:[/green] {f}")
        mp3_files = [f for f in mp3_files if f not in archived_files]

    if mp3_files:
        archive_path = os.path.join(folder, archive_base)
        if dry_run:
            console.print(f"[yellow]Would archive {len(mp3_files)} MP3s into {archive_path}[/yellow]")
            return 0
        
        try:
            cmd, _ = get_archive_command_and_extension(archive_type)
            
            if archive_type.lower() in ["tar.gz", "tar.xz", "tar.bz2"]:
                # For tar formats, we need to create the archive with all files at once
                subprocess.run(cmd + [archive_path] + mp3_files, cwd=folder, check=True)
            elif archive_type.lower() in ["xz", "gzip", "bzip2"]:
                # For single-file compressors, we need to create a tar first, then compress
                temp_tar = os.path.join(folder, "temp.tar")
                subprocess.run(["tar", "-cf", temp_tar] + mp3_files, cwd=folder, check=True)
                subprocess.run(cmd + [temp_tar], cwd=folder, check=True)
                # Rename the compressed file
                compressed_file = temp_tar + archive_ext
                if os.path.exists(compressed_file):
                    os.rename(compressed_file, archive_path)
                if os.path.exists(temp_tar):
                    os.remove(temp_tar)
            else:
                # For 7z and zip formats
                subprocess.run(cmd + [archive_path] + mp3_files, cwd=folder, check=True)
            
            if keep:
                console.print(f"[cyan]{len(mp3_files)} MP3s archived (kept originals) in:[/cyan] {folder}")
            else:
                for f in mp3_files:
                    os.remove(os.path.join(folder, f))
                    if verbose:
                        console.print(f"[green]Archived and deleted:[/green] {f}")
                console.print(f"[cyan]{len(mp3_files)} MP3s archived and deleted in:[/cyan] {folder}")
            return len(mp3_files)
        except Exception as e:
            console.print(f"[red]Error archiving in {folder}: {e}[/red]")
            return 0
    return 0

def scan_archive(root, archive_type="7z", dry_run=False, verbose=False, keep=False):
    total_archived = 0
    folders = []

    for dirpath, _, _ in os.walk(root):
        mp3s = find_matching_mp3s(dirpath)
        if mp3s:
            folders.append((dirpath, mp3s))

    for index, (folder, mp3s) in enumerate(folders, 1):
        console.print(f"\n[{index}/{len(folders)}] {folder}", style="bold")
        archived = archive_and_delete(folder, mp3s, archive_type, dry_run, verbose, keep)
        total_archived += archived

    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Folders scanned: {len(folders)}")
    console.print(f"MP3s archived: {total_archived}")
    console.print(f"Archive format: {archive_type}")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")
    console.print(f"Keep originals: {'Yes' if keep else 'No'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Archive MP3s that duplicate FLACs into various archive formats and optionally delete originals.")
    parser.add_argument("-d", "--directory", required=True, help="Root directory to scan")
    parser.add_argument("--format", default="7z", choices=["7z", "zip", "tar.gz", "tar.xz", "tar.bz2", "xz", "gzip", "bzip2"], 
                       help="Archive format (default: 7z)")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without modifying files")
    parser.add_argument("--verbose", action="store_true", help="Print detailed output per file")
    parser.add_argument("--keep", action="store_true", help="Archive MP3s but keep originals instead of deleting")
    args = parser.parse_args()
    scan_archive(args.directory, args.format, args.dry_run, args.verbose, args.keep)