import yt_dlp
from download_song import download_song_with_metadata

def get_video_urls_from_playlist(yt_link):
    # Initialize yt-dlp options
    ydl_opts = {
        'quiet': True,  # Suppress yt-dlp output
        'extract_flat': True,  # Extract video URLs only (no download)
    }

    # Create a youtube-dl instance with options
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Get information about the YouTube link
            info_dict = ydl.extract_info(yt_link, download=False)

            # Check if it's a playlist
            if 'entries' in info_dict:  # It's a playlist
                video_urls = [entry['url'] for entry in info_dict['entries']]
                return video_urls
            else:
                # It's a single video (not a playlist)
                return [info_dict['url']]
        except Exception as e:
            print(f"Error extracting info from YouTube link: {e}")
            return []

# Example usage:
def inspect_link(url):
    video_urls = get_video_urls_from_playlist(url)
    if video_urls:
        print("Video URLs:", video_urls)
        for url in video_urls:
            download_song_with_metadata(url)
    else:
        print("No video URLs extracted.")
        download_song_with_metadata(url)
