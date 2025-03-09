import subprocess
import requests
import base64
import sys
from embed_metadata import embed_metadata
import re  # To handle regex for removing descriptors
import urllib.parse

# Replace with your Spotify credentials
client_id = ''
client_secret = ''

# Base64 encode the client_id and client_secret
credentials = f"{client_id}:{client_secret}"
encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

# Get access token
url = 'https://accounts.spotify.com/api/token'
headers = {'Authorization': f'Basic {encoded_credentials}'}
data = {'grant_type': 'client_credentials'}

response = requests.post(url, headers=headers, data=data)
access_token = response.json().get('access_token')

if not access_token:
    print("Error: Could not retrieve access token.")
    sys.exit(1)

# Validate input arguments
if len(sys.argv) != 5:
    print(f"Number of arguments: {len(sys.argv)}")
    print("Arguments:", sys.argv)
    print("Usage: python script.py <artist_name> <album_name> <song_name>")
    sys.exit(1)

artist_name = sys.argv[1]
album_name = sys.argv[2]
song_name = sys.argv[3]
file_path = sys.argv[4]

# Sanitize the song title
sanitized_title = re.sub(r'\(original mix\)', '', song_name, flags=re.IGNORECASE)  # Remove "(Original Mix)"
sanitized_title = re.sub(r'[^\w\s-]', '', sanitized_title).strip()  # Remove unwanted characters

# Extract only the first artist's name (before the first comma)
first_artist = artist_name.split(",")[0].strip()  # Get first artist and remove leading/trailing spaces
first_artist = re.sub(r'[^\w\s-]', '', first_artist)  # Remove unwanted characters

# Sanitize the album name
sanitized_album = re.sub(r'[^\w\s-]', '', album_name).strip()

# Encode query for URL
query = f'track:{sanitized_title} artist:{first_artist} album:{sanitized_album}'
encoded_query = urllib.parse.quote(query)

# Build search URL
search_url = f'https://api.spotify.com/v1/search?q={encoded_query}&type=track&limit=1'
headers = {'Authorization': f'Bearer {access_token}'}

print(search_url)  # Debugging: Check the final URL

track_response = requests.get(search_url, headers=headers)
track_data = track_response.json()

# Print full response for debugging
print(track_data)

if 'tracks' in track_data and track_data['tracks']['items']:
    track_info = track_data['tracks']['items'][0]

    # Extract metadata
    track_id = track_info['id']
    track_name = track_info['name']
    album_name = track_info['album']['name']
    release_date = track_info['album']['release_date']
    duration_ms = track_info['duration_ms']
    track_number = track_info['track_number']
    disc_number = track_info['disc_number']
    popularity = track_info['popularity']
    explicit = track_info['explicit']
    isrc = track_info['external_ids'].get('isrc', 'N/A')
    album_art_url = track_info['album']['images'][0]['url'] if track_info['album']['images'] else "No image available"

    # Extract album ID from the track's album object
    album_id = track_info['album']['id']

    # Fetch album details using album ID
    album_url = f'https://api.spotify.com/v1/albums/{album_id}'
    album_response = requests.get(album_url, headers=headers)
    album_data = album_response.json()

    # Example code to check for genres in album data
    album_genre = album_data.get('genres', [])

    # Handle the case when no genres are available for the album
    if album_genre:
        album_genre = album_genre[0]
    else:
        # Fallback to artist genre if album genre is unavailable
        artist_id = album_data['artists'][0]['id']  # Assuming album data has an artist entry
        artist_data = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers).json()
        artist_genres = artist_data.get('genres', [])
        
        if artist_genres:
            album_genre = artist_genres[0]  # Fallback to the first genre of the artist
        else:
            album_genre = 'Genre not available'

    print(f"Album Genre: {album_genre}")

    # Print metadata
    print(f"Title: {track_name}")
    print(f"Artist: {artist_name}")
    print(f"Album: {album_name}")
    print(f"Release Date: {release_date}")
    print(f"Duration: {duration_ms / 1000:.2f} seconds")
    print(f"Track Number: {track_number}")
    print(f"Disc Number: {disc_number}")
    print(f"Popularity: {popularity}")
    print(f"Explicit: {'Yes' if explicit else 'No'}")
    print(f"ISRC: {isrc}")
    print(f"Album Art URL: {album_art_url}")
    print(f"Album Genre: {album_genre}")

    # # Download the album art
    # image_response = requests.get(album_art_url)
    # with open(f"{song_name}_album_art.jpg", 'wb') as file:
    #     file.write(image_response.content)

    # print("Album art downloaded successfully!")

    embed_metadata(
    file_path, 
    track_name, 
    artist_name, 
    album_name, 
    release_date, 
    duration_ms, 
    track_number, 
    disc_number, 
    popularity, 
    explicit, 
    isrc, 
    album_art_url, 
    album_genre
    )
else:
    print("Song not found on Spotify.")
