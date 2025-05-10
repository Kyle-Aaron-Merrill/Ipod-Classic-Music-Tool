import os
import mutagen
from mutagen.easyid3 import EasyID3
from datetime import datetime

# Define keywords for special editions
special_keywords = ["Deluxe", "Expanded", "Remastered", "Special Edition", "Anniversary"]

def find_deluxe_albums(music_folder):
    """
    Scans the folder to find deluxe/special editions of albums.
    Returns a mapping of base album names to their deluxe versions.
    """
    album_mapping = {}

    for filename in os.listdir(music_folder):
        if filename.endswith(".mp3"):
            file_path = os.path.join(music_folder, filename)
            try:
                audio = EasyID3(file_path)
                album = audio.get("album", [""])[0]

                if any(keyword.lower() in album.lower() for keyword in special_keywords):
                    base_album = album.split(" (")[0].strip()
                    album_mapping[base_album] = album

            except mutagen.MutagenError:
                print(f"Skipping: {filename} (Invalid MP3 metadata)")

    return album_mapping

def update_album_metadata(music_folder, album_mapping):
    """
    Updates the album metadata of standard versions to their deluxe counterparts.
    Also reorders track numbers based on creation date.
    """
    album_tracks = {}

    # First pass: Collect files and their creation timestamps
    for filename in os.listdir(music_folder):
        if filename.endswith(".mp3"):
            file_path = os.path.join(music_folder, filename)
            try:
                audio = EasyID3(file_path)
                album = audio.get("album", [""])[0]
                track_num = int(audio.get("tracknumber", ["0"])[0].split("/")[0])

                # Check if album should be updated
                if album in album_mapping:
                    album = album_mapping[album]
                    audio["album"] = album
                    audio.save()

                # Store track info
                creation_time = os.path.getctime(file_path)  # Get file creation time
                album_tracks.setdefault(album, []).append((file_path, creation_time))

            except (mutagen.MutagenError, ValueError):
                print(f"Error processing: {filename}")

    # Second pass: Sort and update track numbers sequentially
    for album, tracks in album_tracks.items():
        tracks.sort(key=lambda x: x[1])  # Sort by creation date
        for index, (file_path, _) in enumerate(tracks, start=1):
            try:
                audio = EasyID3(file_path)
                audio["tracknumber"] = str(index)  # Sequential track numbering
                audio.save()
                print(f"Updated track {index} for album '{album}' in file {os.path.basename(file_path)}")

            except mutagen.MutagenError:
                print(f"Failed to update track number for {os.path.basename(file_path)}")


def process_music_folder(music_folder):
    album_map = find_deluxe_albums(music_folder)
    update_album_metadata(music_folder, album_map)

    print("Album metadata and track numbering update complete!")
