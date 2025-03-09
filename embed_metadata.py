import os
import shutil
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TDRC, TRCK, TPOS, TCON, TXXX
import requests
from io import BytesIO
import magic 
import re  # Import regex for handling song name clean-up

def embed_metadata(file_path, track_name, artist_name, album_name, release_date, duration_ms, 
                   track_number, disc_number, popularity, explicit, isrc, album_art_url, album_genre):
    try:
        audio = MP3(file_path, ID3=ID3)
    except Exception as e:
        print(f"Error loading MP3 file: {e}")
        return
    
    if not audio.tags:
        audio.add_tags()
    
    # Update to ID3 v2.3 (widely supported)
    audio.tags.update_to_v23()
    
    # Add metadata
    audio.tags.add(TIT2(encoding=3, text=track_name))
    audio.tags.add(TPE1(encoding=3, text=artist_name))
    audio.tags.add(TALB(encoding=3, text=album_name))
    audio.tags.add(TDRC(encoding=3, text=release_date))
    audio.tags.add(TRCK(encoding=3, text=str(track_number)))
    audio.tags.add(TPOS(encoding=3, text=str(disc_number)))
    audio.tags.add(TCON(encoding=3, text=album_genre))
    audio.tags.add(TXXX(encoding=3, desc="Popularity", text=str(popularity)))
    audio.tags.add(TXXX(encoding=3, desc="Explicit", text="Yes" if explicit else "No"))
    audio.tags.add(TXXX(encoding=3, desc="ISRC", text=isrc))

    # Download and embed album art
    if album_art_url:
        try:
            response = requests.get(album_art_url)
            if response.status_code == 200:
                image_data = BytesIO(response.content)
                mime_type = magic.Magic(mime=True).from_buffer(image_data.read(2048))
                
                print(f"Detected image MIME type: {mime_type}")  # Debugging

                if mime_type in ['image/jpeg', 'image/png']:
                    audio.tags.add(APIC(encoding=3, mime=mime_type, type=3, desc='Cover', data=image_data.getvalue()))
                else:
                    print("Unsupported image format. Convert to JPEG before embedding.")
            else:
                print("Failed to download album art.")
        except Exception as e:
            print(f"Error fetching album art: {e}")

    # Save changes
    try:
        audio.save(v2_version=3)  # Force ID3 v2.3
        audio = MP3(file_path, ID3=ID3)  # Reload file
        print("Metadata embedded successfully!")
    except Exception as e:
        print(f"Error saving metadata: {e}")

    # Print metadata to verify
    for tag in audio.tags.values():
        print(tag)

        # Simplified path using the user's desktop directory
    desktop = os.path.expanduser("~")  # This will get the user's home directory
    destination_folder = os.path.join(desktop, "Desktop", "metadata_filler", "music")

    try:
        # Create the destination folder if it doesn't exist
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        # Get the file name (without path) and move the file
        destination_path = os.path.join(destination_folder, os.path.basename(file_path))
        shutil.move(file_path, destination_path)  # Move the file
        print(f"File moved to {destination_path}")
    except Exception as e:
        print(f"Error moving file: {e}")
