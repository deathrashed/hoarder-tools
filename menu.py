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
DIRECTORY_PRESETS = [
    "/Volumes/Eksternal/Audio",
    "/Volumes/Eksternal/Audio/Electronic",
    "/Volumes/Eksternal/Audio/Hip-Hop",
    "/Volumes/Eksternal/Audio/Metal",
    "/Volumes/Eksternal/Audio/Miscellaneous",
    "/Volumes/Eksternal/Audio/Punk & Hardcore",
    "/Volumes/Eksternal/Audio/Rock & Grunge",
    "/Volumes/Eksternal/Music/Nicotine+",
    "/Volumes/Eksternal/Music/Deemix",
]
DEFAULT_PRESET_BY_SCRIPT = {
    "metadata_update_genres_lastfm.py": 8,
    "metadata_update_genres_discogs.py": 8,
}

TOOLS = {
    "1": {
        "script": "lyrics_embed_from_lrc.py",
        "label": "Embed LRC Files",
        "category": "Lyrics",
        "description": "Embed `.lrc` lyrics into FLAC and MP3 files",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "2": {
        "script": "lyrics_find_missing_embedded.py",
        "label": "Find Missing Lyrics",
        "category": "Lyrics",
        "description": "List missing lyrics for Lyrics Finder",
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
        "description": "Convert and rename cover files to jpg",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "5": {
        "script": "artist_image_normalize.py",
        "label": "Normalize Artist Images",
        "category": "Cover Art",
        "description": "Rename `folder.jpg` to `artist.jpg`",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "6": {
        "script": "cover_normalize_case.py",
        "label": "Standardize Cover Names",
        "category": "Cover Art",
        "description": "Normalize cover and artist image filenames",
        "arg_pattern": "--archive",
        "supports_dry_run": True,
    },
    "7": {
        "script": "cover_fetch_highres.py",
        "label": "Download HighRes Covers",
        "category": "Cover Art",
        "description": "Fetch replacement cover art with COVIT",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "8": {
        "script": "normalize_backdrops.py",
        "label": "Normalize Backdrop File Names",
        "category": "Cover Art",
        "description": "Renumber backdrops into sequential series",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "9": {
        "script": "folder_remove_empty.py",
        "label": "Delete Folders Without Audio",
        "category": "Cleanup",
        "description": "Delete folders that contain no audio",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "10": {
        "script": "folder_remove_cover_only.py",
        "label": "Remove Empty/Cover-Only Folders",
        "category": "Cleanup",
        "description": "Delete empty folders/only contain cover",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "11": {
        "script": "track_title_split_folder_fix.py",
        "label": "Fix Split Track Title Folders",
        "category": "Cleanup",
        "description": "Fix folders with slashes in track titles",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "12": {
        "script": "archive_lossy_duplicates.py",
        "label": "Archive Lossy Duplicates",
        "category": "Archive",
        "description": "Archive lossy files that match FLAC releases",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "13": {
        "script": "archive_mp3_duplicates.py",
        "label": "Archive MP3 Duplicates",
        "category": "Archive",
        "description": "Archive MP3 files that match FLAC releases",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "14": {
        "script": "track_validate_numbering.py",
        "label": "Check Track Numbering",
        "category": "Quality",
        "description": "Audit filename track-number sequences and gaps",
        "arg_pattern": "--archive",
        "supports_dry_run": True,
    },
    "15": {
        "script": "metadata_generate_nfo.py",
        "label": "Generate Album/Artist Info Files",
        "category": "Metadata",
        "description": "Create stub `album.nfo` and `artist.nfo` files",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "16": {
        "script": "metadata_update_genres_lastfm.py",
        "label": "Update Genres From Last.fm",
        "category": "Metadata",
        "description": "Update MP3 genre tags from Last.fm tags",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "17": {
        "script": "metadata_update_genres_discogs.py",
        "label": "Update Genres From Discogs",
        "category": "Metadata",
        "description": "Update MP3 genre/year tags from Discogs",
        "arg_pattern": "-d",
        "supports_dry_run": True,
    },
    "18": {
        "script": "metal_archives_scraper.py",
        "label": "Download Band Logos/Photos",
        "category": "Assets",
        "description": "Fetch `logo.png` and `artist.jpg` from Metallum",
        "arg_pattern": "path",
        "supports_dry_run": False,
    },
    "19": {
        "script": "acquisition_discography_gaps.py",
        "label": "Find Missing Releases",
        "category": "Acquisition",
        "description": "Compare Deezer discography results against your collection and optionally download gaps",
        "arg_pattern": "-d",
        "supports_dry_run": True,
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

def show_directory_presets(default_index):
    table = Table(title="Directory Presets", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Path", style="green")
    for index, path in enumerate(DIRECTORY_PRESETS, 1):
        label = f"{path} [dim](default)[/dim]" if index == default_index else path
        table.add_row(str(index), label)
    table.add_row("c", "[white]Custom absolute path[/white]")
    console.print()
    console.print(table)
    console.print()


def resolve_directory_selection(base_path, relative_suffix=""):
    directory = os.path.expanduser(base_path.strip())
    if relative_suffix.strip():
        directory = os.path.join(directory, relative_suffix.strip())
    return os.path.normpath(directory)


def get_default_preset_index(script_info):
    return DEFAULT_PRESET_BY_SCRIPT.get(script_info["script"], 1)


def get_music_directory(script_info):
    """Prompt user for music directory using presets plus an optional relative suffix."""
    default_index = get_default_preset_index(script_info)
    console.print("\n[bold cyan]Choose a base directory:[/bold cyan]")
    show_directory_presets(default_index)
    selection = Prompt.ask(
        "Base path",
        default=str(default_index),
    ).strip().lower()

    if selection == "c":
        base_path = Prompt.ask("Custom absolute path", default="")
        if not base_path:
            console.print("[red]Error: Directory is required[/red]")
            return None
    elif selection.isdigit() and 1 <= int(selection) <= len(DIRECTORY_PRESETS):
        base_path = DIRECTORY_PRESETS[int(selection) - 1]
    else:
        console.print(f"[red]Error: Invalid base path selection: {selection}[/red]")
        return None

    relative_suffix = Prompt.ask("Relative subpath (optional)", default="").strip()
    directory = resolve_directory_selection(base_path, relative_suffix)

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
    directory = get_music_directory(script_info)
    if not directory:
        return
    
    # Ask for dry-run
    dry_run = False
    if script_info.get("supports_dry_run", True):
        if script_name == "acquisition_discography_gaps.py":
            dry_run = False
        else:
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

    if script_name == "cover_fetch_highres.py":
        wait_between_albums = Confirm.ask(
            "Wait for confirmation between albums?",
            default=True,
        )
        if not wait_between_albums:
            extra_args.append("--no-wait")

    if script_name in {
        "lyrics_find_missing_embedded.py",
        "artist_image_normalize.py",
        "normalize_backdrops.py",
        "folder_remove_empty.py",
        "folder_remove_cover_only.py",
        "track_title_split_folder_fix.py",
        "metadata_generate_nfo.py",
        "metadata_update_genres_lastfm.py",
        "metadata_update_genres_discogs.py",
        "acquisition_discography_gaps.py",
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

    if script_name == "acquisition_discography_gaps.py":
        band = Prompt.ask("Band or artist name")
        album = Prompt.ask("Known album for artist matching")
        extra_args.extend(["--band", band, "--album", album])
        include_singles = Confirm.ask("Include singles in the discography scan?", default=False)
        if include_singles:
            extra_args.append("--include-singles")
        output_path = Prompt.ask(
            "Output missing-release URL list",
            default="missing_discography_urls.txt",
        )
        if output_path:
            extra_args.extend(["--output", output_path])
        download_missing = Confirm.ask(
            "After the scan, choose specific missing releases to download with deemon?",
            default=False,
        )
        if download_missing:
            extra_args.append("--download-with-deemon")
    
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
