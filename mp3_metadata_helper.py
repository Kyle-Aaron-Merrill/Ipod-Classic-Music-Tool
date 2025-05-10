import os
import datetime
from embed_metadata import embed_metadata
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
import inspect
from PIL import Image
from io import BytesIO


def embed_album_art(new_file_path, relevant_file):
    try:
        # Load the relevant file to extract album art
        audio = MP3(relevant_file, ID3=ID3)
        
        # Check if the file has tags
        if not audio.tags:
            print(f"No tags found in the file: {relevant_file}")
            return
        
        # Extract the album art (APIC frame contains the album art)
        album_art = None
        for tag in audio.tags.values():
            if isinstance(tag, APIC):  # APIC frame contains album art
                album_art = tag.data
                print("Album art found in the relevant file.")
                break  # Exit loop once we find the first album art

        # If album art is found, embed it into the new file
        if album_art:
            new_audio = MP3(new_file_path, ID3=ID3)  # Open the new file for embedding
            if not new_audio.tags:
                new_audio.tags = ID3()  # Create an empty ID3 tag if not present
            
            # Embed the album art into the new file using the APIC frame
            new_audio.tags.add(
                APIC(
                    encoding=1,  # 3 stands for UTF-8 encoding
                    mime="image/jpeg",  # The MIME type of the image (can be 'image/png' or 'image/jpeg')
                    type=3,  # Type 3 is for album art
                    desc="Cover",  # Description of the image
                    data=album_art  # The actual image data
                )
            )
            new_audio.save()  # Save the changes to the new file
            print(f"Album art successfully embedded into {new_file_path}")
        else:
            print("No album art found in the relevant file.")
    except Exception as e:
        print(f"Error embedding album art: {e}")

# Function to get the creation time and metadata from an MP3 file
def get_mp3_metadata(file_path):
    try:
        audio = MP3(file_path)
        creation_date = os.path.getctime(file_path)  # Creation time of the file
        album = audio.get('TALB', ['Unknown Album'])[0]  # Album tag (if present)
        artist = audio.get('TPE1', ['Unknown Artist'])[0]  # Artist tag (if present)
        title = audio.get('TIT2', ['Unknown Title'])[0]  # Title tag (if present)
        track_number = audio.get('TRCK', [None])[0]  # Track number (if present)
        disc_number = audio.get('TPOS', [None])[0]  # Disc number (if present)
        duration_ms = int(audio.info.length * 1000)  # Duration in milliseconds

        # Provide default values for missing parameters
        popularity = 0  # Default value
        explicit = False  # Default value (assumed not explicit)
        isrc = 'N/A'  # Default value
        album_art_url = ''  # Default value (no album art)
        album_genre = album if album != 'Unknown Album' else 'N/A'  # Default genre if missing

        # Convert creation_date to formatted release_date string
        release_date = datetime.datetime.fromtimestamp(creation_date).strftime('%Y-%m-%d')

        return creation_date,title, artist, album, release_date, duration_ms, track_number, disc_number, popularity, explicit, isrc, album_art_url, album_genre
    except Exception as e:
        print(f"Error reading metadata from {file_path}: {e}")
        return None, None, None, None, None, None, None, 0, False, 'N/A', '', 'Unknown'

# Function to calculate the confidence score based on the date difference and metadata similarity
def calculate_confidence(current_date, creation_date, album, current_album, artist, current_artist, current_title, empty_title):

        if album in ['Unknown Album', None] or artist in ['Unknown Artist', None] or current_title == empty_title:
            return 0  # No confidence if metadata is missing

        # Calculate the time difference in seconds
        time_diff = abs(current_date - creation_date)

        # If time difference exceeds 1 minute (60 seconds), do not consider the file as relevant
        if time_diff > 60:
            return 0  # Exclude file if the time difference exceeds 1 minute

        # Limit the time difference to 1 minute (60 seconds) for scaling
        time_diff_factor = max(0.01, 1 - min(time_diff, 60) / 60)  # Factor reduces with time, but max difference is 1 minute

        metadata_factor = 1
        if album == current_album:
            metadata_factor *= 1.5
        if artist == current_artist:
            metadata_factor *= 1.2

        confidence = float(time_diff_factor * metadata_factor)
        return confidence



def has_valid_album_art(file_path):
    try:
        audio = MP3(file_path, ID3=ID3)
        for tag in audio.tags.values():
            if isinstance(tag, APIC):
                if tag.data and len(tag.data) > 0:
                    try:
                        # Try to open and verify the image
                        img = Image.open(BytesIO(tag.data))
                        img.verify()  # This checks for corruption
                        if img.format in ['JPEG', 'PNG']:
                            return True
                    except Exception:
                        continue
        return False
    except Exception as e:
        print(f"Error checking album art in {file_path}: {e}")
        return False

def find_relevant_mp3(new_file_path, music_folder):
    new_metadata = get_mp3_metadata(new_file_path)
    if not new_metadata or not new_metadata[0]:
        print(f"Error: Could not retrieve metadata from {new_file_path}.")
        return None

    (new_creation_date, new_title, new_artist, new_album, new_release_date,
     new_duration_ms, new_track_number, new_disc_number, new_popularity,
     new_explicit, new_isrc, new_album_art_url, new_album_genre) = new_metadata

    relevant_files = []
    for file_name in os.listdir(music_folder):
        file_path = os.path.join(music_folder, file_name)
        if os.path.isfile(file_path) and file_path.endswith('.mp3'):
            metadata = get_mp3_metadata(file_path)
            if not metadata or not metadata[0]:
                continue

            (creation_date, title, artist, album, release_date,
             duration_ms, track_number, disc_number, popularity,
             explicit, isrc, album_art_url, album_genre) = metadata

            confidence = calculate_confidence(
                new_creation_date, creation_date,
                album, new_album,
                artist, new_artist,
                title, new_title
            )
            if confidence > 0 and has_valid_album_art(file_path):
                relevant_files.append((file_path, confidence))

    if not relevant_files:
        return None

    relevant_files.sort(key=lambda x: x[1], reverse=True)
    return relevant_files[0][0]

def process_track_number(track_number):
        track_number = int(track_number) if track_number is not None and track_number.isdigit() else 0

        # Get the name of the caller function
        caller_function = inspect.stack()[2].function

        if caller_function == "cleanUpTool":
            track_number -= 1  # Modify logic if needed
        else:
            track_number += 1

        return track_number

# Function to save metadata to a file based on the most relevant file found
def save_metadata_from_relevant_file(new_file_path, music_folder):
    relevant_file = find_relevant_mp3(new_file_path, music_folder)
    if relevant_file:
        print(f"Found relevant file {relevant_file} to extract metadata from.")
        # Unpack the metadata returned by get_mp3_metadata into individual variables
        creation_date, title, artist, album, release_date, duration_ms, track_number, disc_number, popularity, explicit, isrc, album_art_url, album_genre = get_mp3_metadata(relevant_file)

        if new_file_path and isinstance(new_file_path, str):  # Ensure it's a string
            filename = os.path.basename(new_file_path)  # Extract last part of path
            title = os.path.splitext(filename)[0] if "." in filename else filename  # Remove extension if present
        track_number = process_track_number(track_number)
        duration_ms = get_mp3_metadata(new_file_path)[5]

        # Now create a list with the modified title
        metadata = [title, artist, album, release_date, duration_ms, str(track_number), disc_number, popularity, explicit, isrc, album_art_url, album_genre]

        # Pass the modified metadata to embed_metadata
        embed_metadata(new_file_path, *metadata)
        embed_album_art(new_file_path, relevant_file)

    else:
        print("No relevant file found. Proceeding with default metadata saving.")

# Main function to use the above methods
def main(new_file_path, music_folder):
    if not os.listdir(music_folder):
        print("Music folder is empty. Saving metadata to new file directly.")
        embed_metadata(new_file_path, "N/A", "N/A", "N/A", "Unknown", 0, 0, 0, "N/A", 0, 0, 0, "N/A")
    else:
        save_metadata_from_relevant_file(new_file_path, music_folder)

# Test the function
#music_folder = 'music'  # Change this to your actual music folder path
#new_file_path = 'music/so far ahead ᐳ empire.mp3'  # Path to the new song file you want to save metadata for
#main(new_file_path, music_folder)
