#!/usr/bin/env python3
"""
Interactive menu for running music library management tools.
"""

import os
import sys
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

console = Console()

# Script directory
SCRIPT_DIR = Path(__file__).parent
SCRIPTS_DIR = SCRIPT_DIR / "scripts"

TOOLS = {
    "1": {
        "script": "lyrics_embed_from_lrc.py",
        "label": "Embed Lyrics From LRC Files",
        "category": "Lyrics",
        "description": "Embed `.lrc` lyrics into FLAC and MP3 files",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "2": {
        "script": "lyrics_find_missing_embedded.py",
        "label": "Find Missing Embedded Lyrics",
        "category": "Lyrics",
        "description": "Write a path list of missing tracks and optionally open it in Lyrics Finder",
        "arg_pattern": "-d",
        "supports_dry_run": False,
    },
    "3": {
        "script": "cover_extract_embedded.py",
        "label": "Extract Embedded Cover Art",
        "category": "Cover Art",
        "description": "Save embedded artwork as `cover.jpg`",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "4": {
        "script": "cover_normalize_format.py",
        "label": "Normalize Cover File Format",
        "category": "Cover Art",
        "description": "Convert and rename cover files to a standard format",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "5": {
        "script": "artist_image_normalize.py",
        "label": "Normalize Artist Folder Images",
        "category": "Cover Art",
        "description": "Rename `folder.jpg` to `artist.jpg` and remove duplicates",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "6": {
        "script": "cover_normalize_case.py",
        "label": "Standardize Cover File Names",
        "category": "Cover Art",
        "description": "Normalize cover and artist image filenames",
        "arg_pattern": "--archive",
        "supports_dry_run": True,
    },
    "7": {
        "script": "cover_fetch_highres.py",
        "label": "Download High-Resolution Cover Art",
        "category": "Cover Art",
        "description": "Fetch replacement cover art with COVIT",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "8": {
        "script": "folder_remove_empty.py",
        "label": "Remove Folders Without Audio Files",
        "category": "Cleanup",
        "description": "Delete folders that contain no audio anywhere below them",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "9": {
        "script": "folder_remove_cover_only.py",
        "label": "Remove Empty and Cover-Only Folders",
        "category": "Cleanup",
        "description": "Delete empty folders and folders that only contain cover images",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "10": {
        "script": "track_title_split_folder_fix.py",
        "label": "Fix Split Track Title Folders",
        "category": "Cleanup",
        "description": "Flatten folders created from slashes in track titles",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "11": {
        "script": "archive_lossy_duplicates.py",
        "label": "Archive Lossy Duplicates",
        "category": "Archive",
        "description": "Archive lossy files that match FLAC releases",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "12": {
        "script": "archive_mp3_duplicates.py",
        "label": "Archive MP3 Duplicates",
        "category": "Archive",
        "description": "Archive MP3 files that match FLAC releases",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "13": {
        "script": "track_validate_numbering.py",
        "label": "Check Track Numbering",
        "category": "Quality Control",
        "description": "Audit filename track-number sequences and gaps",
        "arg_pattern": "--archive",
        "supports_dry_run": True,
    },
    "14": {
        "script": "metadata_generate_nfo.py",
        "label": "Generate Album and Artist Info Files",
        "category": "Metadata",
        "description": "Create stub `album.nfo` and `artist.nfo` files",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "15": {
        "script": "metal_archives_scraper.py",
        "label": "Download Band Logos and Photos",
        "category": "Artist Assets",
        "description": "Fetch `logo.png` and `artist.jpg` from Metal Archives",
        "arg_pattern": "path",
        "supports_dry_run": False,
    },
}

LEGACY_TOOLS = [
    ("Remove Lyrics Folders", "archive/lyrics_remove_folders.py"),
    ("Remove Deprecated Cover Formats", "archive/cover_remove_deprecated.py"),
    ("Update Genres From Last.fm", "archive/metadata_fetch_genres_lastfm.py"),
    ("Normalize Featured Artist Tags", "archive/metadata_normalize_multi_artist.py"),
]

def show_menu():
    """Display the main menu."""
    table = Table(title="Music Library Management Tools", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Tool", style="green", width=36)
    table.add_column("Category", style="magenta", width=18)
    table.add_column("Description", style="white", width=46)
    
    for key, tool in sorted(TOOLS.items(), key=lambda x: int(x[0])):
        table.add_row(key, tool["label"], tool["category"], tool["description"])
    
    console.print()
    console.print(table)
    console.print()

def get_music_directory():
    """Prompt user for music directory."""
    console.print("\n[bold cyan]Enter your music library directory:[/bold cyan]")
    directory = Prompt.ask("Directory path", default="")
    
    if not directory:
        console.print("[red]Error: Directory is required[/red]")
        return None
    
    # Expand user home directory
    directory = os.path.expanduser(directory)
    
    if not os.path.isdir(directory):
        console.print(f"[red]Error: Directory does not exist: {directory}[/red]")
        return None
    
    return directory

def build_command(script_info, directory, dry_run=True, extra_args=None):
    """Build the command to run a script."""
    script_path = SCRIPTS_DIR / script_info["script"]
    
    if not script_path.exists():
        console.print(f"[red]Error: Script not found: {script_path}[/red]")
        return None
    
    cmd = [sys.executable, str(script_path)]
    
    # Add directory argument
    if script_info["arg_pattern"] == "-d":
        cmd.extend(["-d", directory])
    elif script_info["arg_pattern"] == "--archive":
        cmd.extend(["--archive", directory])
    elif script_info["arg_pattern"] == "path":
        cmd.append(directory)
    
    # Add dry-run if requested
    if dry_run and script_info.get("supports_dry_run", True):
        cmd.append("--dry-run")
    
    # Add extra arguments
    if extra_args:
        cmd.extend(extra_args)
    
    return cmd


def execute_command(cmd, label):
    """Run a command and print a consistent success or failure message."""
    console.print(f"\n[bold cyan]Running {label}...[/bold cyan]\n")
    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            console.print(f"\n[bold green]✓ {label} completed successfully[/bold green]")
        else:
            console.print(f"\n[bold red]✗ {label} exited with code {result.returncode}[/bold red]")
        return result.returncode
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        return 130
    except Exception as e:
        console.print(f"\n[red]Error running script: {e}[/red]")
        return 1


def maybe_run_for_real_after_dry_run(cmd, label, should_prompt=False):
    """Offer to rerun a successful dry-run command without --dry-run."""
    if not should_prompt or "--dry-run" not in cmd:
        return None

    if not Confirm.ask("Run this script for real now?", default=False):
        return None

    real_cmd = [part for part in cmd if part != "--dry-run"]
    return execute_command(real_cmd, f"{label} (real run)")

def run_script(script_key):
    """Run a selected script."""
    if script_key not in TOOLS:
        console.print(f"[red]Invalid selection: {script_key}[/red]")
        return
    
    script_info = TOOLS[script_key]
    script_name = script_info["script"]
    
    console.print(f"\n[bold green]Selected: {script_info['label']}[/bold green]")
    console.print(f"[dim]{script_info['description']}[/dim]\n")
    
    # Get music directory
    directory = get_music_directory()
    if not directory:
        return
    
    # Ask for dry-run
    dry_run = False
    if script_info.get("supports_dry_run", True):
        dry_run = Confirm.ask("Run in dry-run mode?", default=True)
    
    # Build extra arguments based on script
    extra_args = []
    
    if script_name in {"archive_lossy_duplicates.py", "archive_mp3_duplicates.py"}:
        format_choice = Prompt.ask(
            "Archive format",
            choices=["7z", "zip", "tar.gz", "tar.xz", "tar.bz2", "gzip", "bzip2", "xz"],
            default="tar.xz"
        )
        extra_args.extend(["--format", format_choice])
        
        keep_originals = Confirm.ask("Keep original files?", default=False)
        if keep_originals:
            extra_args.append("--keep")
    
    if script_name == "lyrics_embed_from_lrc.py":
        force = Confirm.ask("Force re-embedding (even if already embedded)?", default=False)
        if force:
            extra_args.append("--force")
        verbose = Confirm.ask("Verbose output?", default=True)
        if verbose:
            extra_args.append("--verbose")

    if script_name in {
        "lyrics_find_missing_embedded.py",
        "artist_image_normalize.py",
        "folder_remove_empty.py",
        "folder_remove_cover_only.py",
        "track_title_split_folder_fix.py",
        "metadata_generate_nfo.py",
    }:
        verbose = Confirm.ask("Verbose output?", default=True)
        if verbose:
            extra_args.append("--verbose")

    if script_name == "lyrics_find_missing_embedded.py":
        output_path = Prompt.ask(
            "Output path list file",
            default="missing_embedded_lyrics.txt",
        )
        extra_args.extend(["--output", output_path])
        prompt_after_scan = Confirm.ask(
            "Prompt to open the saved path list in Lyrics Finder after the scan finishes?",
            default=False,
        )
        if prompt_after_scan:
            extra_args.append("--prompt-open-in-lyrics-finder")

    if script_name == "folder_remove_cover_only.py":
        delete_covers = Confirm.ask("Delete cover images before removing folders?", default=False)
        if delete_covers:
            extra_args.append("--delete-covers")

    if script_name == "track_validate_numbering.py":
        strict = Confirm.ask("Use strict mode (flag albums not starting at 01)?", default=False)
        if strict:
            extra_args.append("--strict")

    if script_name == "metal_archives_scraper.py":
        process_all = Confirm.ask("Process all bands under this path?", default=False)
        if process_all:
            extra_args = ["--all", "--path", directory]
        force = Confirm.ask("Force re-download even if images already exist?", default=False)
        if force:
            extra_args.append("--force")
    
    # Build and show command
    cmd = build_command(script_info, directory, dry_run, extra_args)
    if not cmd:
        return
    
    console.print(f"\n[bold yellow]Command:[/bold yellow] {' '.join(cmd)}\n")
    
    # Confirm execution
    if not Confirm.ask("Execute this command?", default=True):
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    result_code = execute_command(cmd, script_info["label"])
    if result_code == 0 and dry_run:
        maybe_run_for_real_after_dry_run(cmd, script_info["label"], should_prompt=True)

def main():
    """Main menu loop."""
    console.print(Panel.fit(
        "[bold cyan]Music Library Management Tools[/bold cyan]\n"
        "[dim]Grouped tools for music library maintenance[/dim]",
        border_style="cyan"
    ))
    
    while True:
        show_menu()
        
        console.print("[dim]Enter a tool number, 'q' to quit, or 'l' to view legacy tools[/dim]")
        choice = Prompt.ask("\nSelection", default="q").strip().lower()
        
        if choice == "q":
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        elif choice == "l":
            console.print("\n[bold yellow]Legacy / One-Off Tools:[/bold yellow]")
            for label, script_path in LEGACY_TOOLS:
                console.print(f"  • {label} - {script_path}")
            console.print("\n[dim]These are intentionally kept out of the primary menu and can be run directly if needed.[/dim]\n")
        elif choice in TOOLS:
            run_script(choice)
            if not Confirm.ask("\nRun another script?", default=True):
                break
        else:
            console.print(f"[red]Invalid selection: {choice}[/red]\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
