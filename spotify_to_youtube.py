import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from urllib.parse import quote_plus

def setup_chrome_driver():
    """Set up the Chrome WebDriver with headless options."""
    options = Options()
    # options.add_argument('--headless')  # Uncomment to run headless
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280,800')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def get_spotify_metadata(driver, url):
    """Fetch track info and album art from a Spotify track page."""
    driver.get(url)
    time.sleep(2)  # Let page load

    try:
        # Album Art
        album_art_elem = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div/div[2]/div[5]/div/div[2]/div[1]/div/main/section/div[1]/div[2]/div[2]/div/img'))
        )
        album_art_url = album_art_elem.get_attribute("src")

        # Track Title
        title_elem = driver.find_element(By.XPATH, '//*[@id="main"]/div/div[2]/div[5]/div/div[2]/div[1]/div/main/section/div[1]/div[2]/div[3]/span[2]/h1')
        track_title = title_elem.text

        # Artist Name
        artist_elem = driver.find_element(By.XPATH, '//*[@id="main"]/div/div[2]/div[5]/div/div[2]/div[1]/div/main/section/div[1]/div[2]/div[3]/div/div/span/a')
        artist_name = artist_elem.text

        # Album Name
        album_elem = driver.find_element(By.XPATH, '//*[@id="main"]/div/div[2]/div[5]/div/div[2]/div[1]/div/main/section/div[1]/div[2]/div[3]/div/span[2]/a')
        album_name = album_elem.text

        return {
            "title": track_title,
            "artist": artist_name,
            "album": album_name,
            "album_art": album_art_url
        }

    except Exception as e:
        print("❌ Error extracting Spotify metadata:", e)
        return None

def go_to_youtube_search(driver, title, artist, album):
    """Navigate the current tab to the YouTube search results page using full metadata."""
    query = f"{artist} {title} {album}"
    search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    driver.get(search_url)

def extract_youtube_metadata(driver, title, album, artist):
    """Extract metadata from YouTube search results."""
    try:
        # Wait for the video elements to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="items"]'))
        )

        # Extract the title
        album_elem = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/ytd-secondary-search-container-renderer/div/ytd-universal-watch-card-renderer/div[1]/ytd-watch-card-rich-header-renderer/div/div/a/ytd-channel-name/div/div/yt-formatted-string')
        album = album_elem.text

        # Extract the subtitle
        artist_elem = driver.find_element(By.XPATH, '//*[@id="watch-card-subtitle"]/yt-formatted-string')
        artist = artist_elem.text.split("•")[1].strip()

        # Extract the video thumbnail URL
        thumbnail_elem = driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/ytd-secondary-search-container-renderer/div/ytd-universal-watch-card-renderer/div[2]/ytd-watch-card-hero-video-renderer/div/div[1]/ytd-single-hero-image-renderer/yt-img-shadow/img')
        thumbnail_url = thumbnail_elem.get_attribute('src')
        

        # Extract the first video's compact renderer
        result = find_watch_card_by_title(driver, title)
        title = result["matched_title"]
        youtube_link = result["youtube_link"]

        return {
            "album": album,
            "artist": artist,
            "thumbnail_url": thumbnail_url,
            "title": title,
            "youtube_link": youtube_link
        }

    except Exception as e:
        print("❌ Error extracting YouTube metadata via universal watch card:", e)
        print("🔁 Attempting fallback scrape from standard video results...")

        fallback = extract_fallback_youtube_metadata(driver, artist)
        if fallback:
            metadata = fetch_metadata_from_fallback(driver, fallback['youtube_link'])
            print("✅ Fallback metadata extracted:")
            print(fallback)
            if (title == metadata['title'], album == metadata['album'], artist == metadata['artist']):
                return metadata  
        else:
            print("❌ Fallback also failed.")
            return None
        
def strip_title(raw_title):
    # Remove artist name prefix and common suffixes like (Official Music Video), etc.
    clean_title = re.sub(r'^[^-–]*[-–]\s*', '', raw_title)  # Remove "Artist - " or "Artist – "
    clean_title = re.sub(r'\(.*?\)|\[.*?\]', '', clean_title).strip()  # Remove anything in () or []
    


def fetch_metadata_from_fallback(driver, youtube_link):
    """
    Fallback metadata fetcher that opens a YouTube video link, expands the description (if collapsed),
    mutes the video via JavaScript (muting the entire tab), and scrapes metadata fields directly.
    """
    try:
        driver.get(youtube_link)

        # Use JavaScript to mute the video (mute the entire tab's audio)
        driver.execute_script("""
            var video = document.querySelector('video');
            if (video) {
                video.muted = true;
            }
        """)

        # Define XPaths for the elements
        title_xpath = '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-watch-flexy/div[5]/div[1]/div/div[2]/ytd-watch-metadata/div/div[4]/div[1]/div/ytd-text-inline-expander/div[2]/ytd-structured-description-content-renderer/div[3]/ytd-horizontal-card-list-renderer/div[1]/div[2]/div[2]/div/yt-video-attribute-view-model/div/a/div[2]/h1'
        artist_xpath = '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-watch-flexy/div[5]/div[1]/div/div[2]/ytd-watch-metadata/div/div[4]/div[1]/div/ytd-text-inline-expander/div[2]/ytd-structured-description-content-renderer/div[3]/ytd-horizontal-card-list-renderer/div[1]/div[2]/div[2]/div/yt-video-attribute-view-model/div/a/div[2]/h4/span'
        album_xpath = '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-watch-flexy/div[5]/div[1]/div/div[2]/ytd-watch-metadata/div/div[4]/div[1]/div/ytd-text-inline-expander/div[2]/ytd-structured-description-content-renderer/div[3]/ytd-horizontal-card-list-renderer/div[1]/div[2]/div[2]/div/yt-video-attribute-view-model/div/a/div[2]/span/span'
        
        # Wait for the description section and try to expand it if necessary
        description_expander_xpath = '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-watch-flexy/div[5]/div[1]/div/div[2]/ytd-watch-metadata/div/div[4]/div[1]/div/ytd-text-inline-expander/tp-yt-paper-button[1]'

        # Check if the description is collapsed and click to expand
        try:
            description_expander = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, description_expander_xpath))
            )
            if "more" in description_expander.text.lower():  # if the description contains 'more'
                description_expander.click()  # Click to expand
                WebDriverWait(driver, 2).until(
                    EC.text_to_be_present_in_element((By.XPATH, description_expander_xpath), 'Show less')  # Wait for expansion
                )
        except Exception as e:
            print("❌ Error expanding description:", e)
        
        # Wait for elements to be visible after description expansion
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, title_xpath)))

        # Fetch values from the expanded description
        title_elem = driver.find_element(By.XPATH, title_xpath)
        artist_elem = driver.find_element(By.XPATH, artist_xpath)
        album_elem = driver.find_element(By.XPATH, album_xpath)

        title = title_elem.text
        artist = artist_elem.text
        album = album_elem.text

        return {
            "title": title,
            "artist": artist,
            "album": album,
            "youtube_link": youtube_link
        }

    except Exception as e:
        print("❌ Error fetching fallback metadata from video page:", e)
        return None



    
def extract_fallback_youtube_metadata(driver, expected_artist):
    """Search standard video results for a video by matching artist name."""
    try:
        # Wait for the video section to load
        video_section_xpath = '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-search/div[1]/ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[2]/ytd-item-section-renderer/div[3]'
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, video_section_xpath))
        )

        # Find all video renderers in that section
        video_renderers_xpath = f'{video_section_xpath}/ytd-video-renderer'
        video_elements = driver.find_elements(By.XPATH, video_renderers_xpath)

        for video in video_elements:
            try:
                # Extract channel (artist) name
                channel_elem = video.find_element(By.XPATH, './div[1]/div/div[2]/ytd-channel-name/div/div/yt-formatted-string/a')
                channel_name = channel_elem.text.strip()

                if expected_artist.lower() in channel_name.lower():
                    # Artist match found
                    title_elem = video.find_element(By.ID, "video-title")
                    title = title_elem.get_attribute("title")
                    link = title_elem.get_attribute("href")

                    return {
                        "title": title,
                        "artist": channel_name,
                        "youtube_link": link
                    }
            except Exception as inner_e:
                continue  # Skip this video and try next

        print("❌ No fallback video matched the artist name.")
        return None

    except Exception as e:
        print("❌ Fallback YouTube scrape failed:", e)
        return None




def find_watch_card_by_title(driver, target_title):
    """Search through watch cards and return info for the one matching the track title."""
    try:
        cards_xpath = '//ytd-vertical-watch-card-list-renderer//ytd-watch-card-compact-video-renderer'
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, cards_xpath))
        )
        video_cards = driver.find_elements(By.XPATH, cards_xpath)
        
        for card in video_cards:
            try:
                title_elem = card.find_element(By.XPATH, './/yt-formatted-string[1]')
                title_text = title_elem.text.strip()
                if target_title.lower() in title_text.lower():
                    # ✅ Get the link from the <a> tag wrapping the card
                    anchor_elem = card.find_element(By.XPATH, './a')
                    yt_url = anchor_elem.get_attribute("href")
                    return {
                        "matched_title": title_text,
                        "youtube_link": yt_url
                    }
            except:
                continue
        print(f"❌ No watch card matched title: {target_title}")
        return None

    except Exception as e:
        print("❌ Error during card title search:", e)
        return None


# === Example Usage ===
def spotify_to_youtube_main(url):
    driver = setup_chrome_driver()
    
    spotify_url = url
    metadata = get_spotify_metadata(driver, spotify_url)
    
    if metadata:
        print("✅ Metadata Extracted from Spotify:")
        print(metadata)

        # Search YouTube for the song
        go_to_youtube_search(driver, metadata['title'], metadata['artist'], metadata['album'])
        
        # Extract metadata from YouTube search results
        yt_metadata = extract_youtube_metadata(driver, metadata['title'], metadata['album'], metadata['artist'])
        
        if yt_metadata:
            print("✅ YouTube Metadata Extracted:")
            print(yt_metadata)
            return yt_metadata['youtube_link'] 
    driver.quit()


#main("https://open.spotify.com/track/0SjnBEHZVXgCKvOrpvzL2k")