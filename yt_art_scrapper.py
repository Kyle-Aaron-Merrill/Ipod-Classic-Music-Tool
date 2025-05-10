from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def setup_chrome_driver():
    """Set up the Chrome WebDriver with headless options."""
    options = Options()
    #options.add_argument('--headless')  # Use headless mode for Chrome (modern headless setting)
    options.add_argument('--disable-gpu')  # Ensure GPU is disabled in headless mode
    options.add_argument('--window-size=5x5')  # Set window size for screenshots and rendering

    # Set up the driver with ChromeDriverManager to automatically manage the driver version
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def get_album_art_url(driver, ytmusic_url):
    """Extract the album art URL from a YouTube Music URL."""
    driver.get(ytmusic_url)
    time.sleep(5)  # Allow time for page elements to load

    try:
        # Wait for the image element to be present in the DOM using the updated selector
        img_elem = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, '(//img[@id="img"])')  # XPath for the album art image
            )
        )
        # Get the 'src' attribute which contains the URL of the album art
        thumbnail_url = img_elem.get_attribute("src")
        return thumbnail_url
    except Exception as e:
        print("❌ Error extracting album art:", e)
        return None

def art_scrapper_main(url):
    driver = setup_chrome_driver()
    
    try:
        print("🚀 Opening URL:", url)  # Debugging log
        album_art_url = get_album_art_url(driver, url)
        
        if album_art_url:
            print("✅ Album Art URL:", album_art_url)
            return album_art_url
        else:
            print("❌ Failed to extract album art.")
    finally:
        print("🧹 Closing browser.")
        driver.quit()

# if __name__ == "__main__":
#     art_scrapper_main("https://music.youtube.com/watch?v=uS0h--cafLo&si=4j4qWL4JNDF38w7v")
