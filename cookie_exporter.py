import json
import os
import sys
import time
import socket
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from subprocess import Popen

def cookie_main():
    # Determine the correct base directory
    if getattr(sys, 'frozen', False):  # Running as a PyInstaller executable
        BASE_DIR = sys._MEIPASS
    else:  # Running as a normal script
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to config.json
    config_path = os.path.join(BASE_DIR, "config.json")

    # Try to load the config file
    try:
        with open(config_path, "r") as config_file:
            config = json.load(config_file)
            print("Config loaded successfully:", config)
    except FileNotFoundError:
        print(f"❌ Error: Config file not found at {config_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON format")
        sys.exit(1)

    # Define Chrome options to attach to existing session
    chrome_options = Options()
    chrome_options.debugger_address = config['chrome_debugger']['address']

    # Function to check if Chrome debugger is running
    def is_chrome_running(debugger_address):
        try:
            # Try to connect to the debugger port to see if Chrome is running
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((debugger_address.split(":")[0], int(debugger_address.split(":")[1])))
            sock.close()
            return True
        except (socket.error, socket.timeout):
            return False

    # Check if the Chrome debugger is running
    if not is_chrome_running(chrome_options.debugger_address):
        print(f"❌ No Chrome debugger instance running at {chrome_options.debugger_address}")
        print("Starting a new Chrome instance with debugger enabled...")
        
        # Start a new Chrome instance with the debugger enabled
        chrome_driver_path = os.path.join(BASE_DIR, "plugins", "chromedriver-win64", "chromedriver.exe")
        Popen([chrome_driver_path, "--remote-debugging-port=" + str(config['chrome_debugger']['port'])])

        # Wait a few seconds for Chrome to start up
        time.sleep(5)
    else:
        print(f"Chrome debugger instance found at {chrome_options.debugger_address}")

    # Initialize WebDriver without creating a new session
    chrome_driver_path = os.path.join(BASE_DIR, "plugins", "chromedriver-win64", "chromedriver.exe")
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Get all window handles
    window_handles = driver.window_handles

    # Variable to keep track of whether the YouTube Music tab is found
    music_tab_found = False

    for handle in window_handles:
        # Switch to the window
        driver.switch_to.window(handle)
        
        # Check if the current window is the YouTube Music page
        if "music.youtube.com" in driver.current_url:
            music_tab_found = True
            break

    # If the tab was not found, open YouTube Music
    if not music_tab_found:
        driver.get("https://music.youtube.com")  # Open it if not found

    # Get all cookies in the current session and save them in Netscape format
    cookies = driver.get_cookies()

    with open('cookies.txt', 'w') as f:
        f.write("# Netscape HTTP Cookie File\n")
        f.write("# This is a generated file!  Do not edit.\n\n")
        for cookie in cookies:
            domain = cookie['domain']
            if not domain.startswith('.'):
                domain = '.' + domain  # Netscape format requires a leading dot
            # Handle expiry
            expiry = cookie.get('expiry', None)
            if expiry is None:
                # Set to one year from now (365 days)
                expiry = int(time.time()) + 365 * 24 * 60 * 60  # Unix timestamp for one year from now
            elif isinstance(expiry, bool):  # Fix boolean values
                expiry = 0
            else:
                expiry = int(expiry)  # Ensure expiry is an integer
            f.write(f"{domain}\tTRUE\t{cookie.get('path', '/')}\t{str(cookie.get('secure', False)).upper()}\t{expiry}\t{cookie['name']}\t{cookie['value']}\n")

    print("Cookies saved successfully!")

    # Do not quit the browser since we are attached to an existing session
    # driver.quit()  # Comment this out if you want to keep Chrome open
