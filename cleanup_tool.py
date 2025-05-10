import os
import hashlib
from collections import defaultdict, Counter
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error, ID3NoHeaderError

def hash_image(image_data):
    return hashlib.sha256(image_data).hexdigest()

def extract_album_art(file_path):
    try:
        audio = ID3(file_path)
        for tag in audio.values():
            if isinstance(tag, APIC):
                return tag.data
    except error:
        pass
    return None

def set_album_art(file_path, image_data, mime='image/jpeg', desc='Cover', verbose=True):
    try:
        # Try to load existing ID3 tags; create them if missing
        try:
            audio = ID3(file_path)
        except ID3NoHeaderError:
            audio = ID3()
        
        # Remove all existing album art
        audio.delall("APIC")

        # Add new album art
        audio.add(APIC(
            encoding=3,          # UTF-8
            mime=mime,
            type=3,              # Front cover
            desc=desc,
            data=image_data
        ))

        audio.save(file_path, v2_version=3)

        if verbose:
            print(f"✅ Updated album art for: {os.path.basename(file_path)}")
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")

def process_album(files):
    art_map = defaultdict(list)
    art_data_map = {}

    for file in files:
        image_data = extract_album_art(file)
        if image_data:
            h = hash_image(image_data)
            art_map[h].append(file)
            art_data_map[h] = image_data

    if not art_map:
        print("No album art found in this album.")
        return

    # Determine most common album art
    counts = {k: len(v) for k, v in art_map.items()}
    most_common = max(counts.values())
    common_candidates = [k for k, v in counts.items() if v == most_common]

    # Tie-breaking: use the first song's art
    if len(common_candidates) > 1:
        first_file = files[0]
        first_art = extract_album_art(first_file)
        chosen_hash = hash_image(first_art)
        chosen_data = first_art
    else:
        chosen_hash = common_candidates[0]
        chosen_data = art_data_map[chosen_hash]

    # Rewrite inconsistent album art
    for h, file_list in art_map.items():
        if h != chosen_hash:
            for file in file_list:
                set_album_art(file, chosen_data)

def find_albums(folder):
    albums = defaultdict(list)
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(".mp3"):
                full_path = os.path.join(root, file)
                try:
                    audio = MP3(full_path)
                    album = audio.get("TALB")
                    if album:
                        album_name = str(album)
                        albums[album_name].append(full_path)
                except Exception as e:
                    print(f"Skipping {file}: {e}")
    return albums

def cleanup_main(folder):
    albums = find_albums(folder)
    print(f"Found {len(albums)} album(s).")
    for album, files in albums.items():
        print(f"\nProcessing album: {album}")
        process_album(files)

# if __name__ == "__main__":
#     import sys
#     if getattr(sys, 'frozen', False):   #Running as a PyInstaller executable
#         BASE_DIR = sys._MEIPASS
#     else:   #Running as a normal script
#         BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#         music_path = os.path.join(BASE_DIR, "music")
#         cleanup_main(music_path)
