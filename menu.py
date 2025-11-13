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

# Frequent scripts with their descriptions and argument patterns
FREQUENT_SCRIPTS = {
    "1": {
        "name": "lyrics_embed_from_lrc.py",
        "description": "Embed lyrics from .lrc files into audio files",
        "arg_pattern": "-d",
        "common_flags": ["--dry-run", "--verbose", "--force"]
    },
    "2": {
        "name": "cover_extract_embedded.py",
        "description": "Extract embedded cover art from audio files",
        "arg_pattern": "-d",
        "common_flags": ["--dry-run"]
    },
    "3": {
        "name": "cover_normalize_format.py",
        "description": "Normalize cover art formats (PNG to JPG, rename patterns)",
        "arg_pattern": "-d",
        "common_flags": ["--dry-run"]
    },
    "4": {
        "name": "cover_normalize_case.py",
        "description": "Standardize cover art filenames to lowercase",
        "arg_pattern": "--archive",
        "common_flags": ["--dry-run"]
    },
    "5": {
        "name": "cover_fetch_highres.py",
        "description": "Fetch high-resolution cover art using COVIT",
        "arg_pattern": "-d",  # Also accepts --archive
        "common_flags": ["--dry-run"]
    },
    "6": {
        "name": "folder_remove_empty.py",
        "description": "Remove empty folders without audio files",
        "arg_pattern": "-d",
        "common_flags": ["--dry-run", "--verbose"]
    },
    "7": {
        "name": "folder_remove_cover_only.py",
        "description": "Remove folders that are empty or only contain cover images",
        "arg_pattern": "-d",
        "common_flags": ["--dry-run", "--verbose", "--delete-covers"]
    },
    "8": {
        "name": "archive_lossy_duplicates.py",
        "description": "Archive various lossy format duplicates (MP3, AAC, OGG, etc.)",
        "arg_pattern": "-d",
        "common_flags": ["--dry-run", "--format", "--keep"]
    },
    "9": {
        "name": "archive_mp3_duplicates.py",
        "description": "Archive MP3 duplicates of FLAC files",
        "arg_pattern": "-d",
        "common_flags": ["--dry-run", "--format", "--keep", "--verbose"]
    },
    "10": {
        "name": "track_validate_numbering.py",
        "description": "Validate track numbering and detect gaps",
        "arg_pattern": "--archive",
        "common_flags": ["--strict"]
    },
    "11": {
        "name": "metadata_generate_nfo.py",
        "description": "Generate album.nfo and artist.nfo documentation files",
        "arg_pattern": "-d",
        "common_flags": ["--dry-run", "--verbose"]
    },
    "12": {
        "name": "lyrics_fetch_metal_archives.py",
        "description": "Fetch lyrics from Metal Archives and save as .lrc files",
        "arg_pattern": "-d",
        "common_flags": ["--dry-run", "--verbose"]
    }
}

def show_menu():
    """Display the main menu."""
    table = Table(title="Music Library Management Tools", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Script", style="green", width=25)
    table.add_column("Description", style="white", width=60)
    
    for key, script in sorted(FREQUENT_SCRIPTS.items(), key=lambda x: int(x[0])):
        table.add_row(key, script["name"], script["description"])
    
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
    script_path = SCRIPT_DIR / script_info["name"]
    
    if not script_path.exists():
        console.print(f"[red]Error: Script not found: {script_path}[/red]")
        return None
    
    cmd = [sys.executable, str(script_path)]
    
    # Add directory argument
    if script_info["arg_pattern"] == "-d":
        cmd.extend(["-d", directory])
    elif script_info["arg_pattern"] == "--archive":
        cmd.extend(["--archive", directory])
    
    # Add dry-run if requested
    if dry_run:
        cmd.append("--dry-run")
    
    # Add extra arguments
    if extra_args:
        cmd.extend(extra_args)
    
    return cmd

def run_script(script_key):
    """Run a selected script."""
    if script_key not in FREQUENT_SCRIPTS:
        console.print(f"[red]Invalid selection: {script_key}[/red]")
        return
    
    script_info = FREQUENT_SCRIPTS[script_key]
    
    console.print(f"\n[bold green]Selected: {script_info['name']}[/bold green]")
    console.print(f"[dim]{script_info['description']}[/dim]\n")
    
    # Get music directory
    directory = get_music_directory()
    if not directory:
        return
    
    # Ask for dry-run
    dry_run = Confirm.ask("Run in dry-run mode?", default=True)
    
    # Build extra arguments based on script
    extra_args = []
    
    if script_key in ["8", "9"]:  # Archive scripts
        format_choice = Prompt.ask(
            "Archive format",
            choices=["7z", "zip", "tar.gz", "tar.xz", "tar.bz2", "gzip", "bzip2", "xz"],
            default="tar.xz"
        )
        extra_args.extend(["--format", format_choice])
        
        keep_originals = Confirm.ask("Keep original files?", default=False)
        if keep_originals:
            extra_args.append("--keep")
    
    if script_key == "1":  # lyrics_embed
        force = Confirm.ask("Force re-embedding (even if already embedded)?", default=False)
        if force:
            extra_args.append("--force")
        verbose = Confirm.ask("Verbose output?", default=True)
        if verbose:
            extra_args.append("--verbose")
    
    if script_key in ["6", "7", "11", "12"]:  # Scripts with verbose option
        verbose = Confirm.ask("Verbose output?", default=True)
        if verbose:
            extra_args.append("--verbose")
    
    if script_key == "7":  # clean_empty_folders
        delete_covers = Confirm.ask("Delete cover images before removing folders?", default=False)
        if delete_covers:
            extra_args.append("--delete-covers")
    
    if script_key == "10":  # track_gap_checker
        strict = Confirm.ask("Use strict mode (flag albums not starting at 01)?", default=False)
        if strict:
            extra_args.append("--strict")
    
    # Build and show command
    cmd = build_command(script_info, directory, dry_run, extra_args)
    if not cmd:
        return
    
    console.print(f"\n[bold yellow]Command:[/bold yellow] {' '.join(cmd)}\n")
    
    # Confirm execution
    if not Confirm.ask("Execute this command?", default=True):
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    # Run the script
    console.print(f"\n[bold cyan]Running {script_info['name']}...[/bold cyan]\n")
    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            console.print(f"\n[bold green]✓ {script_info['name']} completed successfully[/bold green]")
        else:
            console.print(f"\n[bold red]✗ {script_info['name']} exited with code {result.returncode}[/bold red]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error running script: {e}[/red]")

def main():
    """Main menu loop."""
    console.print(Panel.fit(
        "[bold cyan]Music Library Management Tools[/bold cyan]\n"
        "[dim]Select a tool to run[/dim]",
        border_style="cyan"
    ))
    
    while True:
        show_menu()
        
        console.print("[dim]Enter script number, 'q' to quit, or 'a' to view archive scripts[/dim]")
        choice = Prompt.ask("\nSelection", default="q").strip().lower()
        
        if choice == "q":
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        elif choice == "a":
            console.print("\n[bold yellow]Archive Scripts (infrequent/one-time use):[/bold yellow]")
            console.print("  • lyrics_remove_folders.py - Remove all Lyrics folders")
            console.print("  • cover_remove_deprecated.py - Remove deprecated image formats")
            console.print("  • metadata_fetch_genres_lastfm.py - Fetch genres from Last.fm")
            console.print("  • metadata_normalize_multi_artist.py - Normalize multi-artist tags")
            console.print("  • band-photo-logo/ - Metal Archives scraper")
            console.print("\n[dim]These scripts are in the 'archive' folder and can be run directly if needed.[/dim]\n")
        elif choice in FREQUENT_SCRIPTS:
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

