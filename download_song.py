import yt_dlp
import subprocess
import re  # Regex for title sanitization

# Function to download song with metadata from YouTube Music URL
def download_song_with_metadata(url):
    # Initialize yt-dlp to get metadata first
    with yt_dlp.YoutubeDL() as ydl:
        info_dict = ydl.extract_info(url, download=False)  # Do not download yet

    # Metadata extraction
    title = info_dict.get('title', 'N/A')
    artist = info_dict.get('artist', 'N/A')
    album = info_dict.get('album', 'N/A')
    genre = info_dict.get('genre', 'N/A')
    track_number = info_dict.get('track', 'N/A')
    release_year = info_dict.get('release_year', 'N/A')

    # Strip "(original mix)" from the title
    sanitized_title = re.sub(r'\(original mix\)', '', title, flags=re.IGNORECASE)  # Remove "(original mix)"
    sanitized_title = re.sub(r'[^\w\s-]', '', sanitized_title)  # Remove unwanted characters


    # Print metadata
    print(f"Song: {sanitized_title}")
    print(f"Artist: {artist}")
    print(f"Album: {album}")
    print(f"Genre: {genre}")
    print(f"Track Number: {track_number}")
    print(f"Release Year: {release_year}")

    # Path to the cookies.txt file downloaded by Get Cookies extension
    cookies_file_path = 'cookies.txt'  # Replace with the actual path to the cookies file

    ydl_opts = {
        'cookies': cookies_file_path,  # Use the cookies file
        'format': 'bestaudio/best',
        'outtmpl': f'{sanitized_title}.%(ext)s',
        'extractaudio': True,
        'audioquality': 1,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
            'nopostoverwrites': False
        }],
    }

    # Download the song with the updated file name
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])  # Download the song with the sanitized title

    # Filepath of the downloaded MP3 file
    mp3_filename = f"{sanitized_title}.mp3"

    # Call the script to download and embed the thumbnail into the MP3 file
    subprocess.run([r"venv\Scripts\python.exe", "download_metadata.py", artist, album, sanitized_title, mp3_filename])

    # Optionally, return info if needed
    return info_dict

# Example usage
# url = "https://music.youtube.com/playlist?list=OLAK5uy_kYOau6ivsQh10dsLl8uJEjWfe2a9UMv64&si=wS1BO-SKi7loIwL1"  # Replace with actual YouTube Music URL
# download_song_with_metadata(url)
