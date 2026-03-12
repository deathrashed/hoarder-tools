import os
import sys
import argparse
import subprocess
import time
import re
import plistlib
import select
from pathlib import Path
from urllib.parse import urlencode

# Repo root for shared tools like `bin/covit` and the optional virtualenv.
repo_root = Path(__file__).parent.parent
venv_python = repo_root / "hoarder_env" / "bin" / "python3"
if venv_python.exists() and sys.executable != str(venv_python):
    print("🔄 Auto-activating hoarder environment...")
    os.execv(str(venv_python), [str(venv_python)] + sys.argv)

from PIL import Image
from rich.console import Console
from rich.prompt import Confirm
from mutagen import File as MutagenFile

console = Console()
MIN_WIDTH = 1000
MIN_HEIGHT = 1000
AUDIO_EXTS = [".flac", ".mp3", ".m4a", ".ogg", ".wav"]
REMOTE_AGENT = "hoarder-tools/1.0"
REMOTE_TEXT = "Using Music Hoarders Covers: https://covers.musichoarders.xyz"
DEFAULT_COUNTRY = "US"
DEFAULT_SOURCES = [
    "tidal",
    "bandcamp",
    "itunes",
    "amazonmusic",
    "applemusic",
    "lastfm",
    "soulseek",
    "soundcloud",
    "discogs",
]
COVERS_BASE_URL = "https://covers.musichoarders.xyz/"
DEFAULT_BROWSER = "firefox"
DEFAULT_BROWSER_APP = "Firefox"
DEFAULT_BROWSER_BUNDLE_ID = "org.mozilla.firefox"

def is_audio_file(filename):
    return any(filename.lower().endswith(ext) for ext in AUDIO_EXTS)

def get_cover_dimensions(cover_path):
    try:
        with Image.open(cover_path) as img:
            return img.size
    except Exception:
        return (0, 0)

def find_audio_file(folder):
    for f in sorted(os.listdir(folder)):
        if is_audio_file(f):
            return os.path.join(folder, f)
    return None

def read_cover_query(audio_file):
    try:
        audio = MutagenFile(audio_file)
        if not audio or not getattr(audio, "tags", None):
            return {}

        def read_tag(*keys):
            for key in keys:
                value = audio.tags.get(key)
                if not value:
                    continue
                if isinstance(value, list):
                    return str(value[0]).strip()
                if hasattr(value, "text") and value.text:
                    return str(value.text[0]).strip()
                return str(value).strip()
            return None

        query = {}
        artist = read_tag("artist", "ARTIST", "TPE1")
        album = read_tag("album", "ALBUM", "TALB")
        if artist:
            query["artist"] = artist
        if album:
            query["album"] = album
        return query
    except Exception:
        return {}

def build_covit_command(covit_path, audio_file, query=None, country=DEFAULT_COUNTRY, sources=None):
    source_list = sources or DEFAULT_SOURCES
    command = [
        str(covit_path),
        "--address", "covers.musichoarders.xyz",
        "--browsers", DEFAULT_BROWSER,
        "--input", str(audio_file),
        "--query-country", country,
        "--query-sources", ",".join(source_list),
        "--remote-agent", REMOTE_AGENT,
        "--remote-text", REMOTE_TEXT,
        "--primary-output", "cover",
        "--primary-overwrite",
    ]
    query = query or {}
    if query.get("artist"):
        command.extend(["--query-artist", query["artist"]])
    if query.get("album"):
        command.extend(["--query-album", query["album"]])
    return command

def build_cover_search_url(query=None, country=DEFAULT_COUNTRY, sources=None):
    source_list = sources or DEFAULT_SOURCES
    params = {
        "country": country,
        "sources": ",".join(source_list),
    }
    query = query or {}
    if query.get("artist"):
        params["artist"] = query["artist"]
    if query.get("album"):
        params["album"] = query["album"]
    return f"{COVERS_BASE_URL}?{urlencode(params)}"

def build_remote_cover_search_url(query=None, port=None, country=DEFAULT_COUNTRY, sources=None):
    params = {
        "remote.port": str(port),
        "remote.agent": f"COVIT (2024-08-25) - {REMOTE_AGENT}",
        "remote.text": REMOTE_TEXT,
    }
    query = query or {}
    if query.get("artist"):
        params["artist"] = query["artist"]
    if query.get("album"):
        params["album"] = query["album"]
    params["country"] = country
    params["sources"] = ",".join(sources or DEFAULT_SOURCES)
    return f"{COVERS_BASE_URL}?{urlencode(params)}"

def open_cover_search_in_browser(query=None, country=DEFAULT_COUNTRY, sources=None):
    url = build_cover_search_url(query=query, country=country, sources=sources)
    result = subprocess.run(["open", url], check=False)
    return result.returncode == 0

def open_url_in_browser_app(url, app_name):
    result = subprocess.run(["open", "-a", app_name, url], check=False)
    return result.returncode == 0

def get_default_browser_bundle_id():
    plist_path = Path.home() / "Library/Preferences/com.apple.LaunchServices/com.apple.launchservices.secure.plist"
    if not plist_path.exists():
        return None

    try:
        with plist_path.open("rb") as handle:
            data = plistlib.load(handle)
    except Exception:
        return None

    for item in data.get("LSHandlers", []):
        if item.get("LSHandlerURLScheme") == "https":
            return item.get("LSHandlerRoleAll")
    return None

def extract_listening_port(line):
    match = re.search(r"Listening:\s*(\d+)", line or "")
    if not match:
        return None
    return int(match.group(1))

def launch_covit(command, cwd):
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    deadline = time.time() + 2
    port = None
    while time.time() < deadline and process.poll() is None and process.stdout:
        ready, _, _ = select.select([process.stdout], [], [], 0.2)
        if not ready:
            continue
        line = process.stdout.readline()
        if not line:
            continue
        port = extract_listening_port(line)
        if port is not None:
            break
    time.sleep(0.5)
    return process, port

def should_replace_cover(cover_path):
    if not os.path.exists(cover_path):
        return True
    width, height = get_cover_dimensions(cover_path)
    return width < MIN_WIDTH or height < MIN_HEIGHT

def describe_folder(folder):
    parts = folder.strip(os.sep).split(os.sep)
    if len(parts) >= 3:
        return parts[-3], parts[-2], parts[-1]
    elif len(parts) >= 2:
        return parts[-2], parts[-1], ""
    else:
        return "", parts[-1], ""

def process_album_folder(folder, dry_run=False):
    cover_path = os.path.join(folder, "cover.jpg")
    if should_replace_cover(cover_path):
        audio_file = find_audio_file(folder)
        if audio_file:
            if dry_run:
                return {"status": "would_open", "query": read_cover_query(audio_file)}
            try:
                covit_path = repo_root / "bin" / "covit"
                if not covit_path.exists():
                    return {"status": "error", "message": f"COVIT not found at {covit_path}. Please install COVIT first."}

                query = read_cover_query(audio_file)
                command = build_covit_command(covit_path, audio_file, query=query)
                process, port = launch_covit(command, folder)
                exit_code = process.poll()
                if exit_code not in (None, 0):
                    if open_cover_search_in_browser(query):
                        return {
                            "status": "opened_fallback",
                            "query": query,
                            "message": f"COVIT exited with code {exit_code}; opened Covers in browser instead",
                        }
                    return {
                        "status": "error",
                            "message": f"COVIT exited with code {exit_code}",
                        }
                if port and get_default_browser_bundle_id() != DEFAULT_BROWSER_BUNDLE_ID:
                    remote_url = build_remote_cover_search_url(query=query, port=port)
                    open_url_in_browser_app(remote_url, DEFAULT_BROWSER_APP)
                return {"status": "opened", "query": query}
            except Exception as e:
                return {"status": "error", "message": f"Error opening COVIT: {e}"}
        else:
            return {"status": "error", "message": "No audio file found"}
    else:
        return {"status": "skipped", "message": "Cover already high-res"}

def maybe_prompt_continue(wait_for_user=True):
    if not wait_for_user:
        return True
    return Confirm.ask("Continue to the next album after you finish with this cover?", default=True)

def scan_archive(root_path, dry_run=False, verbose=False, wait_for_user=True):
    folders = []
    for dirpath, _, filenames in os.walk(root_path):
        if any(is_audio_file(f) for f in filenames):
            folders.append(dirpath)

    total = len(folders)
    opened = 0
    skipped = 0
    errors = 0
    stopped_early = False

    for index, folder in enumerate(folders, 1):
        letter, artist, album = describe_folder(folder)
        console.print(f"\n[{index}/{total}] {letter} / {artist} / {album}", style="bold")
        result = process_album_folder(folder, dry_run)

        if result["status"] == "opened":
            query = result.get("query") or {}
            summary = " / ".join(part for part in [query.get("artist"), query.get("album")] if part)
            console.print("[green]Opened COVIT for manual cover selection[/green]")
            if summary:
                console.print(f"[dim]Query:[/dim] {summary}")
            opened += 1
            if not maybe_prompt_continue(wait_for_user=wait_for_user):
                stopped_early = True
                break
        elif result["status"] == "opened_fallback":
            query = result.get("query") or {}
            summary = " / ".join(part for part in [query.get("artist"), query.get("album")] if part)
            console.print(f"[yellow]{result['message']}[/yellow]")
            if summary:
                console.print(f"[dim]Query:[/dim] {summary}")
            opened += 1
            if not maybe_prompt_continue(wait_for_user=wait_for_user):
                stopped_early = True
                break
        elif result["status"] == "would_open":
            query = result.get("query") or {}
            summary = " / ".join(part for part in [query.get("artist"), query.get("album")] if part)
            console.print("[yellow]Would open COVIT for manual cover selection[/yellow]")
            if summary:
                console.print(f"[dim]Query:[/dim] {summary}")
            skipped += 1
        elif result["status"] == "skipped":
            console.print(f"[cyan]{result['message']}[/cyan]")
            skipped += 1
        else:
            console.print(f"[red]{result['message']}[/red]")
            errors += 1

    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Folders scanned: {total}")
    console.print(f"COVIT windows opened: {opened}")
    console.print(f"Skipped (high-res or dry-run): {skipped}")
    console.print(f"Errors: {errors}")
    if stopped_early:
        console.print("Stopped early: Yes")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch high-res cover art using COVIT.")
    parser.add_argument("-d", "--directory", help="Root directory to scan")
    parser.add_argument("--archive", help="Archive directory to scan (alternative to -d)")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without launching COVIT")
    parser.add_argument("--verbose", action="store_true", help="Reserved for future verbosity toggle")
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Do not pause for confirmation between albums",
    )
    args = parser.parse_args()
    
    # Determine the directory to scan
    target_dir = args.directory or args.archive
    if not target_dir:
        print("❌ Error: Please specify a directory with -d or --archive")
        sys.exit(1)
        
    scan_archive(target_dir, args.dry_run, args.verbose, wait_for_user=not args.no_wait)
