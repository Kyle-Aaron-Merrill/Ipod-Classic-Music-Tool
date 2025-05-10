import os
import eyed3

# Function to update song metadata
def update_song_metadata(file_path):
    # Load the mp3 file
    audio_file = eyed3.load(file_path)
    
    if audio_file.tag is None:
        audio_file.tag = eyed3.id3.tag.Tag(file_path)
    
    # Get the current artist and album artist metadata
    artist = audio_file.tag.artist
    album_artist = audio_file.tag.album_artist
    
    if artist and artist != '':
        artists = artist.split(',')  # Split if there are multiple artists (comma-separated)
        first_artist = artists[0].strip()  # First artist
        remaining_artists = ', '.join([artist.strip() for artist in artists[1:]])  # Remaining artists
        
        # Set the first artist as the main artist
        audio_file.tag.artist = first_artist
        
        # Set the remaining artists as the album artist
        if remaining_artists:
            if album_artist:
                audio_file.tag.album_artist += ", " + remaining_artists
            else:
                audio_file.tag.album_artist = remaining_artists
    
        # Save the updated metadata
        audio_file.tag.save()

# Function to process all mp3 files in a folder
def process_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".mp3"):
            file_path = os.path.join(folder_path, filename)
            print(f"Processing {filename}...")
            update_song_metadata(file_path)
            print(f"Updated {filename} metadata")


