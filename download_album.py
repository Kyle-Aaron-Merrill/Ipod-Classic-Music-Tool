import subprocess
import json
import sys
import os

def search_album(artist, album, year):
    """Searches YouTube Music for an album and retrieves the playlist URL"""
    search_query = f"{artist} {album} {year} album"
    print(f"🔎 Searching for: {search_query}")

    # Run yt-dlp search and extract JSON metadata
    result = subprocess.run(
        [get_yt_dlp_path(), "--default-search", "ytsearch10", "--skip-download", "-J", f"ytsearch10:{search_query}"],
        capture_output=True, text=True
    )
    
    try:
        data = json.loads(result.stdout)
        for entry in data.get("entries", []):
            # Check if result is a playlist (album)
            if "playlist" in entry.get("url", ""):
                return entry["url"]  # Return first album match
    except json.JSONDecodeError:
        print("❌ Error decoding JSON.")
        return None

    return None

def download_album(album_url):
    """Downloads the album from YouTube Music"""
    print(f"📥 Downloading album from {album_url}")
    subprocess.run([
        get_yt_dlp_path(),
        "-f", "bestaudio",
        "--extract-audio",
        "--audio-format", "mp3",
        "--embed-metadata",
        "--embed-thumbnail",
        album_url
    ])

def get_yt_dlp_path():
    """Returns the correct path to yt-dlp executable"""
    if getattr(sys, 'frozen', False):  # Running as a PyInstaller executable
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # If yt-dlp is packaged with the executable, reference it correctly
    yt_dlp_path = os.path.join(base_path, "yt-dlp")
    if not os.path.isfile(yt_dlp_path):
        yt_dlp_path = "yt-dlp"  # Use system-wide yt-dlp if not packaged
    
    return yt_dlp_path

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python download_album.py '<Artist>' '<Album>' '<Year>'")
        sys.exit(1)

    artist, album, year = sys.argv[1], sys.argv[2], sys.argv[3]
    album_url = search_album(artist, album, year)

    if album_url:
        download_album(album_url)
    else:
        print("❌ Album not found on YouTube Music.")
