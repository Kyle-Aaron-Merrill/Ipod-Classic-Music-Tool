import requests
from mutagen.mp3 import MP3
from io import BytesIO
import magic
from mutagen.id3 import ID3, COMM, TPUB, TENC, WCOP, TCOP, TPE3, TCOM, TMOO, TKEY, TBPM, TPOS, TCON, TXXX, TXXX, APIC, TIT2, TPE1, TALB, TDRC, TRCK
from chat_gpt import get_all_metadata

def embed_metadata(file_path, metadata, album_art_url,track_num,yt_album_name):
    try:
        audio = MP3(file_path, ID3=ID3)  # Make sure ID3 is correctly imported at the top
    except Exception as e:
        print(f"Error loading MP3 file: {e}")
        return

    # Ensure ID3 tags exist
    if audio.tags is None:
        audio.add_tags()
    elif not audio.tags:
        audio.tags.update_to_v23()

    # Define a function to clean non-ASCII characters if necessary
    def strip_hex_chars(input_string):
        if isinstance(input_string, str):
            return ''.join(char for char in input_string if ord(char) < 128)
        else:
            return str(input_string)  # Convert integers to strings

    def set_txxx(tag, desc, value):
        audio.tags.add(TXXX(encoding=3, desc=desc, text=value))

    # Set metadata values
    metadata_cleaned = {
        'title': strip_hex_chars(metadata['title']),
        'subtitle': strip_hex_chars(metadata['subtitle']),
        'comments': strip_hex_chars(metadata['comments']),
        'contributing_artist': strip_hex_chars(metadata['contributing_artist']),
        'album_artist': strip_hex_chars(metadata['album_artist']),
        'album': strip_hex_chars(metadata['album']),
        'genre': strip_hex_chars(metadata['genre']),
        'publisher': strip_hex_chars(metadata['publisher']),
        'encoded_by': strip_hex_chars(metadata['encoded_by']),
        'author_url': strip_hex_chars(metadata['author_url']),
        'copyright': strip_hex_chars(metadata['copyright']),
        'parental_rating_reason': strip_hex_chars(metadata['parental_rating_reason']),
        'composers': strip_hex_chars(metadata['composers']),
        'conductors': strip_hex_chars(metadata['conductors']),
        'group_description': strip_hex_chars(metadata['group_description']),
        'mood': strip_hex_chars(metadata['mood']),
        'part_of_set': strip_hex_chars(metadata['part_of_set']),
        'initial_key': strip_hex_chars(metadata['initial_key'])
    }

    # Apply cleaned metadata to the audio file
    audio.tags.setall('TIT2', [TIT2(encoding=3, text=metadata_cleaned['title'])])  # Title
    audio.tags.setall('TPE1', [TPE1(encoding=3, text=metadata_cleaned['contributing_artist'])])  # Contributing Artist
    audio.tags.setall('TALB', [TALB(encoding=3, text=yt_album_name)])  # Album
    audio.tags.setall('TDRC', [TDRC(encoding=3, text=str(metadata['year']))])  # Year
    audio.tags.setall('TRCK', [TRCK(encoding=3, text=str(track_num))])  # Track Number
    audio.tags.setall('TCON', [TCON(encoding=3, text=metadata_cleaned['genre'])])  # Genre

      # Custom TXXX fields
    # Standard ID3 tag replacements:
    if 'comments' in metadata_cleaned:
        audio['COMM'] = COMM(encoding=3, lang='eng', desc='', text=metadata_cleaned['comments'])

    if 'publisher' in metadata_cleaned:
        audio['TPUB'] = TPUB(encoding=3, text=metadata_cleaned['publisher'])

    if 'encoded_by' in metadata_cleaned:
        audio['TENC'] = TENC(encoding=3, text=metadata_cleaned['encoded_by'])

    if 'author_url' in metadata_cleaned:
        audio['WOAR'] = WCOP(encoding=3, url=metadata_cleaned['author_url'])  # Author URL as WOAR

    if 'copyright' in metadata_cleaned:
        audio['TCOP'] = TCOP(encoding=3, text=metadata_cleaned['copyright'])

    if 'parental_rating_reason' in metadata_cleaned:
        set_txxx(audio, 'Parental Rating', metadata_cleaned['parental_rating_reason'])  # No standard tag; keep as TXXX

    if 'composers' in metadata_cleaned:
        audio['TCOM'] = TCOM(encoding=3, text=metadata_cleaned['composers'])

    if 'conductors' in metadata_cleaned:
        audio['TPE3'] = TPE3(encoding=3, text=metadata_cleaned['conductors'])

    if 'group_description' in metadata_cleaned:
        set_txxx(audio, 'Group Description', metadata_cleaned['group_description'])  # No standard tag

    if 'mood' in metadata_cleaned:
        audio['TMOO'] = TMOO(encoding=3, text=metadata_cleaned['mood'])

    if 'part_of_set' in metadata_cleaned:
        audio['TPOS'] = TPOS(encoding=3, text=metadata_cleaned['part_of_set'])

    if 'initial_key' in metadata_cleaned:
        audio['TKEY'] = TKEY(encoding=3, text=metadata_cleaned['initial_key'])

    if 'beats_per_minute_bpm' in metadata:
        audio['TBPM'] = TBPM(encoding=3, text=str(metadata['beats_per_minute_bpm']))

    if 'protected' in metadata:
        set_txxx(audio, 'Protected', str(metadata['protected']))  # No standard ID3 tag

    if 'part_of_compilation' in metadata:
        audio['TCMP'] = TXXX(encoding=3, desc='TCMP', text=str(metadata['part_of_compilation']))  # unofficial tag used by iTunes



    # Save changes
    try:
        audio.save()
        print("Metadata embedded successfully!")
    except Exception as e:
        print(f"Error saving metadata: {e}")

    # Download and embed album art
    if album_art_url:
        try:
            response = requests.get(album_art_url)
            if response.status_code == 200:
                image_data = BytesIO(response.content)
                mime_type = magic.Magic(mime=True).from_buffer(image_data.read(2048))

                if mime_type in ['image/jpeg', 'image/png']:
                    audio.tags.add(APIC(encoding=3, mime=mime_type, type=3, desc='Cover', data=image_data.getvalue()))
                else:
                    print("Unsupported image format. Convert to JPEG before embedding.")
            else:
                print("Failed to download album art.")
        except Exception as e:
            print(f"Error fetching album art: {e}")

    try:
        audio.save(v2_version=3)  # Force ID3 v2.3
        print("Album art and metadata saved successfully!")
    except Exception as e:
        print(f"Error saving album art: {e}")


# if __name__ == '__main__':
#     def get_gpt_metadata():
#         # Create the metadata dictionary
#         test_metadata = {
#             "title": "Goes By So Fast",
#             "contributing_artist": "Toro y Moi",
#             "album": "MAHAL",
#             "year": "2022"
#         }

#         # Fetch filled metadata from the OpenAI model
#         metadata = get_all_metadata(test_metadata)  # Fetch metadata using OpenAI model

#         # Process the metadata
#         processed_metadata = {
#             "title": metadata.get("title", ""),
#             "subtitle": metadata.get("subtitle", ""),
#             "rating": metadata.get("rating", 0),
#             "comments": metadata.get("comments", ""),
#             "contributing_artist": metadata.get("contributing_artist", ""),
#             "album_artist": metadata.get("album_artist", ""),
#             "album": metadata.get("album", ""),
#             "year": metadata.get("year", 0),
#             "track_number": metadata.get("track_number", 0),
#             "genre": metadata.get("genre", ""),
#             "length": metadata.get("length", ""),
#             "bit_rate": metadata.get("bit_rate", 0),
#             "publisher": metadata.get("publisher", ""),
#             "encoded_by": metadata.get("encoded_by", ""),
#             "author_url": metadata.get("author_url", ""),
#             "copyright": metadata.get("copyright", ""),
#             "parental_rating_reason": metadata.get("parental_rating_reason", ""),
#             "composers": ', '.join(metadata.get("composers", [])),  # Convert list to string
#             "conductors": ', '.join(metadata.get("conductors", [])),  # Convert list to string
#             "group_description": metadata.get("group_description", ""),
#             "mood": metadata.get("mood", ""),
#             "part_of_set": metadata.get("part_of_set", ""),
#             "initial_key": metadata.get("initial_key", ""),
#             "beats_per_minute_bpm": metadata.get("beats_per_minute_bpm", 0),
#             "protected": metadata.get("protected", False),
#             "part_of_compilation": metadata.get("part_of_compilation", False)
#         }

#         # Return the processed metadata
#         return processed_metadata
    
#     embed_metadata("Doom Boom.mp3", get_gpt_metadata(),"https://lh3.googleusercontent.com/bOFkoCDJ1_SRQsZeoyz2py4qsKztfXU5qfDF_ZpJJeyKKBrEYT8IIUdW6Zk3KtBATRyATXd1h8yx71rFXg=w544-h544-l90-rj",1)