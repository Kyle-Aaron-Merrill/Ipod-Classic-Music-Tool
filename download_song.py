import os
import sys
import yt_dlp
import subprocess
import re  # Regex for title sanitization
import time
from download_metadata import main
from cookie_exporter import cookie_main


# Get the absolute path to python.exe in your virtual environment or bundled exe
if getattr(sys, 'frozen', False):  # Running as a PyInstaller executable
    venv_python_path = sys.executable  # or set to your python path
else:
    venv_python_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'Scripts', 'python.exe')

# Initialize the download counter
download_count = 0

# Function to sanitize the song title by replacing special characters
def sanitize_title(title):
    title = re.sub(r'[<>:"///|?*]', '_', title)  # Remove invalid filename characters
    title = title.replace('?', '')  # Replace the question mark explicitly
    title = title.strip()  # Remove leading/trailing spaces
    return title

# Function to update cookies by running cookie_exporter.py
def update_cookies():
    print("Updating cookies...")
    try:
        cookie_main()
        print("Cookies updated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to update cookies: {e}")


# Function to download song with metadata from YouTube Music URL
def download_song_with_metadata(url, track_num, proxy=None, retry=True, total=1):
    # Check and handle shortened "browse" URLs
   # Determine the correct base directory
    if getattr(sys, 'frozen', False):  # Running as a PyInstaller executable
        BASE_DIR = sys._MEIPASS
    else:  # Running as a normal script
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to config.json
    cookies_file_path = os.path.join(BASE_DIR, "cookies.txt")

    cookies_file_path = 'C:/Users/Gamer/Desktop/metadata_filler/cookies.txt'
    
    ydl_opts = {
        'cookiefile': cookies_file_path
    }

    if proxy:
        ydl_opts['proxy'] = proxy if proxy.startswith("http") else f"http://{proxy}"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            print(f"Using Proxy: {proxy}") if proxy else print("No proxy used.")
            print("Metadata extracted successfully:", info_dict["title"])

            global download_count
            download_count += 1
            print(f"Number of songs downloaded: {download_count}")

    except (yt_dlp.utils.ExtractorError, yt_dlp.utils.DownloadError) as e:
        print("ERROR:", e)
        print(f"Total songs downloaded before error: {download_count}")
        error_message = str(e)  # Store the error message first

        # Check if the error is related to authentication, premium restriction, or age restriction
        if any(msg in error_message for msg in [
            "Login required", "403 Forbidden", "Premium", 
            "Sign in to confirm your age", "This video may be inappropriate", "Video unavailable"
        ]):
            print("Authentication, Premium restriction, or Age restriction detected. Attempting to update cookies...")
            update_cookies()

            if retry:
                print("Retrying download after updating cookies...")
                time.sleep(2)  # Small delay before retrying
                return download_song_with_metadata(url, track_num, proxy, retry=False)

        return None

    title = info_dict.get('title', 'N/A')
    artist = info_dict.get('artist', 'N/A')
    album = info_dict.get('album', 'N/A')
    genre = info_dict.get('genre', 'N/A')
    track_number = info_dict.get('track', 'N/A')
    release_year = info_dict.get('release_year', 'N/A')

    sanitized_title = sanitize_title(title)

    print(f"Song: {sanitized_title}")
    print(f"Artist: {artist}")
    print(f"Album: {album}")
    print(f"Genre: {genre}")
    print(f"Track Number: {track_number}")
    print(f"Release Year: {release_year}")

    ydl_opts.update({
        'format': 'bestaudio/best',
        'outtmpl': f'{sanitized_title}.%(ext)s',
        'extractaudio': True,
        'audioquality': 1,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
            'nopostoverwrites': False
        }]
    })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        print(f"Download failed: {e}")
        print("Attempting to update cookies...")
        update_cookies()
        if retry:
                print("Retrying download after updating cookies...")
                time.sleep(2)  # Small delay before retrying
                return download_song_with_metadata(url, track_num, proxy, retry=False)
        
        return None
        


    mp3_filename = f"{sanitized_title}.mp3"

    # Get the absolute path to python.exe in your virtual environment
    venv_python_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'Scripts', 'python.exe')

    # Get the absolute path to download_metadata.py
    download_metadata_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'download_metadata.py')

    print("Python Path:", venv_python_path)
    print("Download Metadata Path:", download_metadata_path)
    print("File Exists:", os.path.exists(download_metadata_path))


    # Run subprocess with absolute path
    subprocess.run([venv_python_path, download_metadata_path, artist, album, sanitized_title, mp3_filename, str(track_num), str(release_year),url])

    return info_dict
