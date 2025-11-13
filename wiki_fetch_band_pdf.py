#!/usr/bin/env python3
"""
Fetch Wikipedia pages as PDF for bands in selected folders.
"""

import os
import sys
import argparse
import subprocess
import urllib.parse
import urllib.request
import json
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# User-Agent header required by Wikipedia
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def make_request(url, timeout=10):
    """Make HTTP request with proper User-Agent header."""
    request = urllib.request.Request(url)
    request.add_header('User-Agent', USER_AGENT)
    return urllib.request.urlopen(request, timeout=timeout)

def select_folder_dialog():
    """Show macOS folder picker dialog and return selected path."""
    script = '''
    tell application "Finder"
        activate
        set folderPath to choose folder with prompt "Select a band folder or directory:"
        return POSIX path of folderPath
    end tell
    '''
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def search_wikipedia(query):
    """Search Wikipedia for a page title matching the query."""
    # First, try direct page lookup (exact match)
    direct_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(query.replace(' ', '_'))
    
    try:
        with make_request(direct_url, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read())
                return data.get('title')
    except urllib.error.HTTPError:
        pass
    except Exception:
        pass
    
    # If direct lookup fails, use search API
    search_api_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json&srlimit=5"
    
    try:
        with make_request(search_api_url, timeout=10) as response:
            data = json.loads(response.read())
            if 'query' in data and 'search' in data['query'] and len(data['query']['search']) > 0:
                # Return the first (most relevant) result
                return data['query']['search'][0]['title']
    except Exception:
        pass
    
    return None

def download_wikipedia_pdf(page_title, output_path):
    """Download Wikipedia page as PDF using the REST API."""
    # Wikipedia REST API PDF endpoint
    pdf_url = f"https://en.wikipedia.org/api/rest_v1/page/pdf/{urllib.parse.quote(page_title.replace(' ', '_'))}"
    
    try:
        with make_request(pdf_url, timeout=30) as response:
            if response.status == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.read())
                return True
            else:
                console.print(f"[red]Failed to download PDF: HTTP {response.status}[/red]")
                return False
    except urllib.error.HTTPError as e:
        if e.code == 404:
            console.print(f"[yellow]Page not found: {page_title}[/yellow]")
        else:
            console.print(f"[red]HTTP error {e.code}: {e.reason}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]Error downloading PDF: {e}[/red]")
        return False

def extract_band_name(folder_path):
    """Extract band name from folder path."""
    folder_name = os.path.basename(folder_path.rstrip('/'))
    # Remove common suffixes that might not be part of the band name
    # You can customize this based on your folder naming conventions
    return folder_name

def process_folder(folder_path, dry_run=False, verbose=False):
    """Process a single folder - search Wikipedia and download PDF."""
    band_name = extract_band_name(folder_path)
    pdf_path = os.path.join(folder_path, 'wiki.pdf')
    
    # Skip if PDF already exists
    if os.path.exists(pdf_path) and not dry_run:
        if verbose:
            console.print(f"[dim]⏭️  Skipping {band_name} - wiki.pdf already exists[/dim]")
        return False
    
    if verbose:
        console.print(f"[cyan]🔍 Searching Wikipedia for: {band_name}[/cyan]")
    
    # Search for Wikipedia page
    page_title = search_wikipedia(band_name)
    
    if not page_title:
        console.print(f"[yellow]❌ No Wikipedia page found for: {band_name}[/yellow]")
        return False
    
    if verbose:
        console.print(f"[green]✓ Found: {page_title}[/green]")
    
    if dry_run:
        console.print(f"[yellow]Would download PDF to: {pdf_path}[/yellow]")
        return True
    
    # Download PDF
    if download_wikipedia_pdf(page_title, pdf_path):
        console.print(f"[green]✓ Downloaded wiki.pdf for: {band_name}[/green]")
        return True
    else:
        return False

def process_directory(root_path, dry_run=False, verbose=False, recursive=True):
    """Process all band folders in a directory."""
    root_path = Path(root_path)
    
    if not root_path.exists():
        console.print(f"[red]Error: Path does not exist: {root_path}[/red]")
        return
    
    folders_to_process = []
    
    # Check if root_path itself is a band folder (has audio files)
    has_audio = any(f.suffix.lower() in ['.flac', '.mp3', '.m4a', '.ogg', '.wav'] 
                    for f in root_path.iterdir() if f.is_file())
    
    if has_audio:
        # This is a band folder, process it directly
        folders_to_process.append(root_path)
    else:
        # This is a directory, find all band folders
        if recursive:
            for folder in root_path.iterdir():
                if folder.is_dir():
                    # Check if folder contains audio files
                    has_audio = any(f.suffix.lower() in ['.flac', '.mp3', '.m4a', '.ogg', '.wav'] 
                                  for f in folder.iterdir() if f.is_file())
                    if has_audio:
                        folders_to_process.append(folder)
        else:
            # Only check immediate subdirectories
            for folder in root_path.iterdir():
                if folder.is_dir():
                    folders_to_process.append(folder)
    
    if not folders_to_process:
        console.print(f"[yellow]No band folders found in: {root_path}[/yellow]")
        return
    
    console.print(f"[bold]Found {len(folders_to_process)} band folder(s) to process[/bold]\n")
    
    successful = 0
    failed = 0
    skipped = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Processing folders...", total=len(folders_to_process))
        
        for folder in folders_to_process:
            result = process_folder(str(folder), dry_run, verbose)
            if result is True:
                successful += 1
            elif result is False:
                if os.path.exists(os.path.join(folder, 'wiki.pdf')):
                    skipped += 1
                else:
                    failed += 1
            progress.update(task, advance=1)
    
    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Successful: {successful}")
    console.print(f"Failed: {failed}")
    console.print(f"Skipped: {skipped}")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch Wikipedia pages as PDF for bands in selected folders."
    )
    parser.add_argument(
        "-d", "--directory",
        help="Directory or band folder to process (if not provided, will show folder picker)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without downloading files"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output per folder"
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Only process immediate subdirectories (not recursive)"
    )
    
    args = parser.parse_args()
    
    # Get directory
    if args.directory:
        directory = args.directory
    else:
        console.print("[bold]Select a band folder or directory:[/bold]")
        directory = select_folder_dialog()
        if not directory:
            console.print("[red]No folder selected. Exiting.[/red]")
            sys.exit(1)
    
    process_directory(
        directory,
        dry_run=args.dry_run,
        verbose=args.verbose,
        recursive=not args.no_recursive
    )

