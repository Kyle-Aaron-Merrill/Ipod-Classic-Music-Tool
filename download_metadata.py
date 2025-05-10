import os
import shutil
import time
import requests
import base64
import sys
from embed_metadata import embed_metadata
import re  # To handle regex for removing descriptors
import urllib.parse
import string
import musicbrainzngs
import json  # For saving metadata to a file
from mp3_metadata_helper import main
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
import uuid
import eyed3
from chat_gpt import get_all_metadata
from yt_art_scrapper import art_scrapper_main

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
    sys.exit(1)
except json.JSONDecodeError:
    print("❌ Error: Invalid JSON format")
    sys.exit(1)

# Set the user agent from the config.json
musicbrainzngs.set_useragent(config['user_agent']['application'], config['user_agent']['version'], config['user_agent']['email'])

# Extract Spotify credentials from the config.json
client_id = config['spotify_credentials']['client_id']
client_secret = config['spotify_credentials']['client_secret']

# Print to verify the extracted values
print("User Agent Set:", config['user_agent'])
print("Spotify Credentials:", client_id, client_secret)

# Base64 encode the client_id and client_secret
credentials = f"{client_id}:{client_secret}"
encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

# Get access token
url = 'https://accounts.spotify.com/api/token'
headers = {'Authorization': f'Basic {encoded_credentials}'}
data = {'grant_type': 'client_credentials'}

def get_spotify_access_token(retries=5, timeout=10):
    """
    Fetch Spotify access token with retry logic.
    """
    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, data=data, timeout=timeout)

            # If successful, return the token
            if response.status_code == 200:
                return response.json().get('access_token')

            print(f"Attempt {attempt + 1} failed: {response.status_code} - {response.text}")
        
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed due to network error: {e}")

        # Wait before retrying (exponential backoff)
        wait_time = 2 ** attempt
        print(f"Retrying in {wait_time} seconds...")
        time.sleep(wait_time)

    print("Error: Could not retrieve access token after multiple attempts.")
    sys.exit(1)

# Call the function to get the token
access_token = get_spotify_access_token()

if not access_token:
    print("Error: Could not retrieve access token.")
    sys.exit(1)

# Function to validate arguments
def validate_args():
    if len(sys.argv) != 8:
        print("Usage: python script.py <artist_name> <album_name> <song_name> <file_path>")
        return False
    return True

# Main script logic wrapped in if __name__ == "__main__":
if __name__ == '__main__':
    # Only validate args and exit if the script is being run directly
    if not validate_args():
        sys.exit(1)

    yt_artist_name = sys.argv[1]
    yt_album_name = sys.argv[2]
    yt_song_name = sys.argv[3]
    file_path = sys.argv[4]
    track_num = int(sys.argv[5])
    yt_release_year = int(sys.argv[6])
    yt_url = sys.argv[7]

    title = ""
    subtitle = ""
    rating = ""
    comments = ""
    contributing_artist = ""
    album_artist = ""
    album = ""
    year = ""
    track_number = ""
    genre = ""
    length = ""
    bit_rate = ""
    publisher = ""
    encoded_by = ""
    author_url = ""
    copyright = ""
    parental_rating_reason = ""
    composers = ""
    conductors = ""
    group_description = ""
    mood = ""
    part_of_set = ""
    initial_key = ""
    beats_per_minute_bpm = ""
    protected = ""
    part_of_compilation = ""
    isrc = ""



    first_artist = yt_artist_name.split(",")[0].strip()

    def symbols_to_unicode_decimal(text):
        return "".join(f"%{ord(char):02X}" if char in string.punctuation else char for char in text)

    sanitized_album = symbols_to_unicode_decimal(yt_album_name)
    sanitized_first_artist = symbols_to_unicode_decimal(first_artist)
    sanitized_title = symbols_to_unicode_decimal(yt_song_name)


    def search_spotify(query):
        search_url = f'https://api.spotify.com/v1/search?q={urllib.parse.quote(query)}&type=track&limit=1'
        track_response = requests.get(search_url, headers={'Authorization': f'Bearer {access_token}'})
        return track_response.json()

    def search_musicbrainz(yt_song_title, yt_artist_name, yt_album_name):
        base_url = "https://musicbrainz.org/ws/2/recording/"
        query = f'"{yt_song_title}" AND artist:{yt_artist_name} AND release:{yt_album_name}'
        params = {
            "query": query,
            "fmt": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "Generation-dl/1.0 (your-email@example.com)"
        }
        response = requests.get(base_url, params=params, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def fetch_album_art(release_id):
        cover_art_url = f"https://coverartarchive.org/release/{release_id}"
        response = requests.get(cover_art_url)

        if response.status_code == 200:
            data = response.json()
            if 'images' in data and len(data['images']) > 0:
                return data['images'][0]['image']
            else:
                return "No album art available"
        else:
            return f"Error fetching album art: {response.status_code}"
    
    def clear_metadata(file_path):
        try:
            audio = MP3(file_path, ID3=ID3)
            if audio.tags:
                audio.delete()  # Remove all metadata
                audio.tags.clear()
                audio.save()
                print(f"Metadata removed from: {file_path}")
            else:
                print(f"No metadata found in: {file_path}")
        except Exception as e:
            print(f"Error removing metadata: {e}")


    def move_file_safely(file_path, destination_folder):
        """
        Moves a file to the destination folder.
        If a file with the same name already exists there,
        it appends a unique identifier to the filename to avoid overwriting.
        """
        # Ensure the destination folder exists
        os.makedirs(destination_folder, exist_ok=True)

        # Get the original file name and extension
        filename, ext = os.path.splitext(os.path.basename(file_path))
        new_filename = filename + ext
        new_file_path = os.path.join(destination_folder, new_filename)

        # Add a unique suffix if a file with the same name already exists
        while os.path.exists(new_file_path):
            unique_id = uuid.uuid4().hex[:8]
            new_filename = f"{filename}_{unique_id}{ext}"
            new_file_path = os.path.join(destination_folder, new_filename)

        # Move the file
        try:
            shutil.move(file_path, new_file_path)
            print(f"File moved to: {new_file_path}")
            return new_file_path
        except Exception as e:
            print(f"Error moving file: {e}")
            return None


    def get_mp3_duration(filepath):
            if not os.path.exists(filepath):
                print(f"❌ File not found: {filepath}")
                return 0

            audio_file = eyed3.load(filepath)
            if audio_file is None or audio_file.info is None:
                print(f"❌ Could not load audio info for: {filepath}")
                return 0

            return audio_file.info.time_secs
    
    def check_for_metadata_errors(yt_album_name, album_name):
         # Compare yt_album_name with album_name
        if yt_album_name.lower() != album_name.lower():
            print(f"Album mismatch: YouTube Album Name: {yt_album_name}, Spotify Album Name: {album_name}")
            # You can decide what to do here. For example, retry or log the mismatch.
            return False
        else:
            return True
        
    def get_gpt_metadata(title, contributing_artist, album, year):
        # Create the metadata dictionary
        test_metadata = {
            "title": title,
            "contributing_artist": contributing_artist,
            "album": album,
            "year": year
        }

        # Fetch filled metadata from the OpenAI model
        metadata = get_all_metadata(test_metadata)  # Fetch metadata using OpenAI model

        # Process the metadata
        processed_metadata = {
            "title": metadata.get("title", ""),
            "subtitle": metadata.get("subtitle", ""),
            "rating": metadata.get("rating", 0),
            "comments": metadata.get("comments", ""),
            "contributing_artist": metadata.get("contributing_artist", ""),
            "album_artist": metadata.get("album_artist", ""),
            "album": metadata.get("album", ""),
            "year": metadata.get("year", 0),
            "track_number": metadata.get("track_number", 0),
            "genre": metadata.get("genre", ""),
            "length": metadata.get("length", ""),
            "bit_rate": metadata.get("bit_rate", 0),
            "publisher": metadata.get("publisher", ""),
            "encoded_by": metadata.get("encoded_by", ""),
            "author_url": metadata.get("author_url", ""),
            "copyright": metadata.get("copyright", ""),
            "parental_rating_reason": metadata.get("parental_rating_reason", ""),
            "composers": ', '.join(metadata.get("composers", [])),  # Convert list to string
            "conductors": ', '.join(metadata.get("conductors", [])),  # Convert list to string
            "group_description": metadata.get("group_description", ""),
            "mood": metadata.get("mood", ""),
            "part_of_set": metadata.get("part_of_set", ""),
            "initial_key": metadata.get("initial_key", ""),
            "beats_per_minute_bpm": metadata.get("beats_per_minute_bpm", 0),
            "protected": metadata.get("protected", False),
            "part_of_compilation": metadata.get("part_of_compilation", False)
        }

        # Return the processed metadata
        return processed_metadata
    
    def get_all_gpt_metadata(title, contributing_artist, album, year):
        # Create the metadata dictionary
        test_metadata = {
            "title": title,
            "contributing_artist": contributing_artist,
            "album": album,
            "year": year
        }

        # Fetch filled metadata from the OpenAI model
        metadata = get_all_metadata(test_metadata)

        # Process the metadata
        processed_metadata = {
            "title": metadata.get("title", ""),
            "subtitle": metadata.get("subtitle", ""),
            "rating": metadata.get("rating", 0),
            "comments": metadata.get("comments", ""),
            "contributing_artist": metadata.get("contributing_artist", ""),
            "album_artist": metadata.get("album_artist", ""),
            "album": metadata.get("album", ""),
            "year": metadata.get("year", 0),
            "track_number": metadata.get("track_number", 0),
            "disc_number": metadata.get("disc_number", 0),
            "genre": metadata.get("genre", ""),
            "length": metadata.get("length", ""),
            "bit_rate": metadata.get("bit_rate", 0),
            "publisher": metadata.get("publisher", ""),
            "encoded_by": metadata.get("encoded_by", ""),
            "author_url": metadata.get("author_url", ""),
            "copyright": metadata.get("copyright", ""),
            "parental_rating_reason": metadata.get("parental_rating_reason", ""),
            "composers": ', '.join(metadata.get("composers", [])),
            "conductors": ', '.join(metadata.get("conductors", [])),
            "group_description": metadata.get("group_description", ""),
            "mood": metadata.get("mood", ""),
            "part_of_set": metadata.get("part_of_set", ""),
            "initial_key": metadata.get("initial_key", ""),
            "beats_per_minute_bpm": metadata.get("beats_per_minute_bpm", 0),
            "protected": metadata.get("protected", False),
            "part_of_compilation": metadata.get("part_of_compilation", False),
            "isrc": isrc if isrc is not None else "",
            "album_art_url": metadata.get("spotify_album_art_url", "")
        }

        return processed_metadata

        
            
    
    song_found = False
    query = f'track:{yt_song_name} artist:{first_artist} album:{yt_album_name}'
    track_data = search_spotify(query)

    if not track_data.get('tracks', {}).get('items', []):
        print("No results found, retrying with sanitized search...")
        query = f'track:{sanitized_title} artist:{sanitized_first_artist} album:{sanitized_album}'
        track_data = search_spotify(query)

    if track_data.get('tracks', {}).get('items', []):
        track_info = track_data['tracks']['items'][0]
        title = track_info['name']
        album = track_info['album']['name']
        release_date = track_info['album']['release_date']
        track_number = track_info['track_number']
        disc_number = track_info['disc_number']
        isrc = track_info['external_ids'].get('isrc', 'N/A')
        album_art_url = track_info['album']['images'][0]['url'] if track_info['album']['images'] else "No image available"
        new_metadata = get_gpt_metadata(title=yt_song_name, contributing_artist=first_artist, album=yt_album_name, year=release_date)
        song_found = True

    if not song_found:
        print("No song found, retrying search before embeding...")
        new_metadata = get_all_gpt_metadata(title=yt_song_name, contributing_artist=first_artist, album=yt_album_name, year="n/a")
        album_art_url = art_scrapper_main(yt_url)
        song_found = True


    if song_found:
        embed_metadata(file_path,new_metadata,album_art_url,track_num,yt_album_name)
        print("Song found! Metadata embedded.")
        move_file_safely(file_path, music_path)

    
