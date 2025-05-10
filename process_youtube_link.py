import json
import os
import sys
import yt_dlp
from download_song import download_song_with_metadata
import time
from fix_album_artist import process_folder
from mp3_metadata_helper import save_metadata_from_relevant_file
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, error
from cleanup_tool import cleanup_main
from sort_albums import process_music_folder
from spotify_to_youtube import spotify_to_youtube_main

# Determine the correct base directory
if getattr(sys, 'frozen', False):  # Running as a PyInstaller executable
    BASE_DIR = sys._MEIPASS
else:  # Running as a normal script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to config.json
config_path = os.path.join(BASE_DIR, "config.json")
music_path = os.path.join(BASE_DIR, "music")

# Try to load the config file
try:
    with open(config_path, "r") as config_file:
        config = json.load(config_file)
        print("Config loaded successfully:", config)
except FileNotFoundError:
    print(f"❌ Error: Config file not found at {config_path}")
except json.JSONDecodeError:
    print("❌ Error: Invalid JSON format")

def get_video_urls_from_playlist(yt_link):
    # Initialize yt-dlp options
    ydl_opts = {
        'quiet': True,  # Suppress yt-dlp output
        'extract_flat': True,  # Extract video URLs only (no download)
    }

    # Create a youtube-dl instance with options
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Get information about the YouTube link
            info_dict = ydl.extract_info(yt_link, download=False)

            # Check if it's a playlist
            if 'entries' in info_dict:  # It's a playlist
                video_urls = [entry['url'] for entry in info_dict['entries']]
                return video_urls
            else:
                # It's a single video (not a playlist)
                return [info_dict['url']]
        except Exception as e:
            print(f"Error extracting info from YouTube link: {e}")
            return []

import time

# Function to load proxies from the config file
def load_proxies():
    try:
            return config.get('proxies', [])
    except Exception as e:
        print(f"Error loading config file: {e}")
        return []
    
proxies = load_proxies()

def handle_spotify_link(link):
    if "/track/" in link:
        return [link]  # ✅ It's already a track link
    elif "/album/" in link:
        return get_spotify_links(link)  # 🔄 Convert album to track links
    else:
        raise ValueError("❌ Unsupported Spotify link: must be a track or album URL.")

def get_spotify_links(album_link):
    # You can add your actual logic here to fetch track links from the album
    return ["https://open.spotify.com/track/xyz123", "https://open.spotify.com/track/abc456"]


def inspect_link(url, progress_bar, progress_label):
    if "open.spotify.com" in url:
        spotify_urls = handle_spotify_link(url)
        index = 0
        total = len(spotify_urls)
        for url in spotify_urls:
            new_url = spotify_to_youtube_main(url)
            if len(proxies) > 0:
                    current_proxy = proxies[(index // 5) % len(proxies)]
            else:
                print("No proxies available!")
                current_proxy = None  # Or set to a default proxy, if available

            # Print the current proxy (for debugging)
            print(f"Using proxy: {current_proxy}")

            # Update song count label
            progress_label.config(text=f"Song: {index + 1} / {total}")

            # Update the proxy in your downloader function (assuming download_song_with_metadata accepts a proxy)
            download_song_with_metadata(new_url, (index + 1), current_proxy, total)

            # Update progress bar
            speed = 1  # Adjust based on your logic
            if index < total:
                time.sleep(0.05)
                progress_bar['value'] += (speed / total) * 100

            index += 1
    else:
        video_urls = get_video_urls_from_playlist(url)
        
        if video_urls:
            print("Video URLs:", video_urls)
            index = 0
            total = len(video_urls)
            for url in video_urls:
                if len(proxies) > 0:
                    current_proxy = proxies[(index // 5) % len(proxies)]
                else:
                    print("No proxies available!")
                    current_proxy = None  # Or set to a default proxy, if available

                # Print the current proxy (for debugging)
                print(f"Using proxy: {current_proxy}")

                # Update song count label
                progress_label.config(text=f"Song: {index + 1} / {total}")

                # Update the proxy in your downloader function (assuming download_song_with_metadata accepts a proxy)
                download_song_with_metadata(url, (index + 1), current_proxy, total)

                # Update progress bar
                speed = 1  # Adjust based on your logic
                if index < total:
                    time.sleep(0.05)
                    progress_bar['value'] += (speed / total) * 100

                index += 1
            
            # This will now only run once after the loop completes
            #cleanUpTool()

        else:
            print("No video URLs extracted.")
            download_song_with_metadata(url, 1, 1)

    # Clean up after this download attempt
    process_music_folder(music_path)
    cleanup_main(music_path)
    