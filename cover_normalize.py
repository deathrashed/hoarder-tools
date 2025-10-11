import os
import argparse
from PIL import Image
from rich.console import Console

console = Console()

AUDIO_EXTENSIONS = {".flac", ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".aif", ".aiff"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

def is_audio_file(filename):
    return os.path.splitext(filename)[1].lower() in AUDIO_EXTENSIONS

def is_image_file(filename):
    return os.path.splitext(filename)[1].lower() in IMAGE_EXTENSIONS

def convert_to_jpg(path, dry_run=False):
    try:
        if dry_run:
            return "Would convert to JPG"
        img = Image.open(path)
        rgb = img.convert("RGB")
        new_path = os.path.splitext(path)[0] + ".jpg"
        rgb.save(new_path, "JPEG", quality=90)
        os.remove(path)
        return f"Converted to JPG: {new_path}"
    except Exception as e:
        return f"Error converting {path}: {e}"

def safe_rename(src, dest_folder, dry_run=False):
    dest_path = os.path.join(dest_folder, "cover.jpg")
    if not os.path.exists(dest_path):
        if dry_run:
            return f"Would rename {os.path.basename(src)} → cover.jpg"
        os.rename(src, dest_path)
        return f"Renamed {os.path.basename(src)} → cover.jpg"
    else:
        return f"Skipped rename (cover.jpg already exists)"

def normalize_album_folder(folder, dry_run=False):
    actions = []
    for f in os.listdir(folder):
        lower = f.lower()
        full_path = os.path.join(folder, f)

        if lower.startswith("cdart.") and is_image_file(f):
            try:
                if dry_run:
                    actions.append(f"Would delete cdart: {full_path}")
                else:
                    os.remove(full_path)
                    actions.append(f"Deleted cdart: {full_path}")
            except Exception as e:
                actions.append(f"Error deleting cdart {full_path}: {e}")
            continue

        if f == "logo.png":
            continue

        if lower.endswith(".png"):
            actions.append(convert_to_jpg(full_path, dry_run))
            continue

        if lower in {"folder.jpg", "folder.jpeg", "album cover.jpg", "album cover.jpeg", "albumartsmall.jpg"} or lower.endswith(".jpeg"):
            actions.append(safe_rename(full_path, folder, dry_run))
    return actions

def normalize_artist_folder(folder, dry_run=False):
    artist_image = os.path.join(folder, "folder.jpg")
    dest_path = os.path.join(folder, "artist.jpg")
    if os.path.exists(artist_image):
        try:
            if dry_run:
                return [f"Would rename artist folder.jpg → artist.jpg"]
            os.rename(artist_image, dest_path)
            return [f"Renamed artist folder.jpg → artist.jpg"]
        except Exception as e:
            return [f"Error renaming artist image: {e}"]
    return []

def describe_folder(folder):
    parts = folder.strip(os.sep).split(os.sep)
    if len(parts) >= 3:
        return parts[-3], parts[-2], parts[-1]
    elif len(parts) >= 2:
        return parts[-2], parts[-1], ""
    else:
        return "", parts[-1], ""

def scan_archive(root, dry_run=False, verbose=False):
    folders = []
    for dirpath, _, filenames in os.walk(root):
        if any(is_audio_file(f) for f in filenames):
            folders.append((dirpath, True))
        elif "folder.jpg" in [f.lower() for f in filenames]:
            folders.append((dirpath, False))

    total = len(folders)
    cleaned = 0

    for index, (folder, is_album) in enumerate(folders, 1):
        letter, artist, album = describe_folder(folder)
        console.print(f"\n[{index}/{total}] {letter} / {artist} / {album}", style="bold")

        actions = normalize_album_folder(folder, dry_run) if is_album else normalize_artist_folder(folder, dry_run)
        if actions:
            cleaned += 1
            for line in actions:
                console.print(f"[green]{line}[/green]")
        else:
            console.print("[cyan]No changes needed[/cyan]")

    console.print("\n[bold underline]Summary[/bold underline]")
    console.print(f"Folders scanned: {total}")
    console.print(f"Folders cleaned: {cleaned}")
    console.print(f"Dry run: {'Yes' if dry_run else 'No'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize cover image formats and naming.")
    parser.add_argument("-d", "--directory", required=True, help="Root directory to scan")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without making changes")
    parser.add_argument("--verbose", action="store_true", help="Reserved for future verbosity toggle")
    args = parser.parse_args()
    scan_archive(args.directory, args.dry_run, args.verbose)