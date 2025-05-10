import json
import time
import tkinter as tk
from tkinter import ttk
import webbrowser
import os
import sys
import io
import threading
import queue
from process_youtube_link import inspect_link  
from tkinterdnd2 import TkinterDnD, DND_FILES, DND_ALL  # Import DND_ALL for text drops
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

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
except json.JSONDecodeError:
    print("❌ Error: Invalid JSON format")

# Create the main application window
root = TkinterDnD.Tk()
root.title("Music Fetcher")
root.geometry("800x700")
root.configure(bg='#0d0221')

# Make columns expandable
root.columnconfigure(0, weight=1)

# Define colors
neon_pink = "#ff007f"
neon_blue = "#00eaff"
neon_purple = "#9d00ff"
button_bg = "#222222"  # Dark button background
button_fg = "#ffffff"  # White text

# Function to handle YouTube link
def open_youtube():
    url = yt_link.get()
    if url:
        progress_bar["value"] = 1  # Start progress
        threading.Thread(target=handle_youtube_link, args=(url,), daemon=True).start()

def handle_youtube_link(url):
    q.put(f"Processing YouTube Link: {url}\n")  # Queue the output
    inspect_link(url, progress_bar, progress_label)


def open_drag_and_drop_window():
    drop_window = tk.Toplevel(root)  # Create a new pop-up window
    drop_window.title("Drag and Drop")
    drop_window.geometry("800x350")  # Increased height to fit the button
    drop_window.configure(bg='#0d0221')

    label = tk.Label(drop_window, text="Drag and Drop Area", fg=neon_blue, bg="#0d0221", font=("Helvetica", 16, "bold"))
    label.pack(pady=10)

    drop_area = tk.Listbox(drop_window, width=70, height=10, bg="black", fg="white", font=("Courier", 12))
    drop_area.pack(pady=10)

    # Register both files and text (URLs) as drop targets using DND_ALL
    drop_window.drop_target_register(DND_FILES, DND_ALL)
    drop_window.dnd_bind('<<Drop>>', lambda event: handle_file_or_url_drop(event, drop_area))

    # Download Button
    download_button = ttk.Button(drop_window, text="Download", style="TButton", command=lambda: process_download(drop_area))
    download_button.pack(pady=10)

def handle_file_or_url_drop(event, drop_area):
    dropped_data = event.data.strip()
    
    # Check if it's a file path or URL
    if dropped_data.startswith(("http://", "https://")):
        drop_area.insert(tk.END, f"URL: {dropped_data}")
        print(f"Dropped URL: {dropped_data}")
    else:
        drop_area.insert(tk.END, f"File: {dropped_data}")
        print(f"Dropped file: {dropped_data}")
    
    update_drop_area_size(drop_area)  # Adjust size dynamically

def update_drop_area_size(drop_area):
    item_count = drop_area.size()
    new_height = min(max(5, item_count), 20)  # Min 5, Max 20 lines
    drop_area.config(height=new_height)


# Function to check for "browse" in the URL and return the full URL if it's a shortened YouTube Music link
def handle_browse_url(url):
    if 'browse' in url:  # Check if the link contains "browse"
        print(f"Detected 'browse' in URL: {url}")
        
        # Set Chrome options to disable pop-up blocking and connect to an existing Chrome session
        chrome_options = Options()
        chrome_options.debugger_address = config['chrome_debugger']['address']
        # Get the directory where the script is located
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # Construct the relative path dynamically
        driver_path = os.path.join(BASE_DIR, "plugins", "chromedriver-win64", "chromedriver.exe")
        # Pass the correct Service object
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Open new tab
        driver.execute_script("window.open('');")  # Open a blank new tab
        driver.switch_to.window(driver.window_handles[-1])  # Switch to the new tab
        driver.get(url)  # Navigate to the URL in the new tab

        # Wait for the URL to fully load
        time.sleep(2)  # Adjust this delay if necessary
        full_url = driver.current_url
        driver.close()  # Close the tab
        driver.switch_to.window(driver.window_handles[0])  # Return to the main tab
        return full_url


# Add label for total progress bar
total_progress_label = tk.Label(root, text="URL: 0 / 0", fg=neon_blue, bg="#0d0221", font=("Helvetica", 12, "bold"))
total_progress_label.grid(row=5, column=0, pady=(0, 5), padx=20, sticky="w")  # Positioned above total progress bar

# Add a second progress bar for overall progress
total_progress_bar = ttk.Progressbar(root, orient="horizontal", length=600, mode="determinate")
total_progress_bar.grid(row=6, column=0, pady=10, padx=20, sticky="ew")  # Positioned below the first one

def process_download(drop_area):
    items = drop_area.get(0, tk.END)  # Get all dropped items
    if not items:
        print("No items to download.")
        return
    
    urls = [item.replace("URL: ", "") for item in items if item.startswith("URL: ")]

    if not urls:
        print("No valid URLs found.")
        return

    progress_bar["value"] = 0  # Reset per-file progress
    total_progress_bar["value"] = 0  # Reset overall progress
    total_progress_bar["maximum"] = len(urls)  # Set max value to total URLs
    total_progress_label.config(text=f"URL: 0 / {len(urls)}")  # Update label initially

    def download_links():
        for i, url in enumerate(urls):
            progress_bar["value"] = 0  # Reset before each download
            converted_url = handle_browse_url(url)  # Convert before processing
            # Update total progress and label
            total_progress_bar["value"] += 1
            total_progress_label.config(text=f"URL: {total_progress_bar['value']} / {len(urls)}")
            handle_youtube_link(converted_url)

            root.after(100, lambda i=i: drop_area.delete(i))  # Remove URL from the listbox
            print(f"Download completed for: {url}")

            

        total_progress_bar["value"] = len(urls)  # Ensure full completion
        progress_bar["value"] = 0  # Reset individual progress
        total_progress_label.config(text=f"URL: {len(urls)} / {len(urls)}")  # Ensure it shows full completion
        print(f"Finished Process")

    threading.Thread(target=download_links, daemon=True).start()  # Run in background



# Header Label
label = tk.Label(root, text="YDL GUI", fg=neon_blue, bg="#0d0221", font=("Helvetica", 24, "bold"))
label.grid(row=0, column=0, pady=10)

# YouTube Link Input Field & Button
yt_frame = tk.Frame(root, bg='#0d0221')
yt_frame.grid(row=1, column=0, pady=10, padx=20, sticky="ew")

yt_link = tk.Entry(yt_frame, width=60, font=("Helvetica", 12))
yt_link.pack(side="left", expand=True, fill="x", padx=5)

yt_button = tk.Button(yt_frame, text="Download", font=("Helvetica", 12, "bold"), bg=neon_pink, fg="white", 
                      activebackground=neon_purple, activeforeground="white", command=open_youtube)
yt_button.pack(side="right", padx=5)

# Button Frame
button_frame = tk.Frame(root, bg="#0d0221")
button_frame.grid(row=2, column=0, pady=10, padx=20, sticky="ew")

buttons = [
    ("Home", None),
    ("Search", lambda: webbrowser.open("https://music.youtube.com/")),
    ("Downloads", lambda: os.path.join(BASE_DIR, "music")),
    ("Drag & Drop", open_drag_and_drop_window)
]

for btn_text, command in buttons:
    btn = tk.Button(button_frame, text=btn_text, font=("Helvetica", 12, "bold"), 
                    bg=button_bg, fg=button_fg, activebackground=neon_purple, activeforeground="white",
                    command=command, width=15)
    btn.pack(side="left", padx=5, pady=5, expand=True)

progress_label = tk.Label(root, text="Song: 0 / 0", fg=neon_blue, bg="#0d0221", font=("Helvetica", 12, "bold"))
progress_label.grid(row=3, column=0, pady=(0, 5), padx=20, sticky="w")  # Positioned above total progress bar

# Progress Bar
progress_bar = ttk.Progressbar(root, orient="horizontal", length=600, mode="determinate")
progress_bar.grid(row=4, column=0, pady=10, padx=20, sticky="ew")

# Terminal Output
terminal_label = tk.Label(root, text="Terminal Output", fg=neon_blue, bg="#0d0221", font=("Helvetica", 12, "bold"))
terminal_label.grid(row=7, column=0, pady=5, padx=20, sticky="w")

terminal = tk.Text(root, height=8, width=80, bg="#111111", fg="white", font=("Courier New", 10), wrap="word")
terminal.grid(row=8, column=0, pady=5, padx=20, sticky="ew")
terminal.config(state=tk.DISABLED)

# Function to periodically check queue & update terminal
q = queue.Queue()
class QueueRedirect(io.StringIO):
    def write(self, text):
        q.put(text)  # Put the text in the queue
        sys.__stdout__.write(text)  # Also print to the real terminal

sys.stdout = QueueRedirect()
sys.stderr = QueueRedirect()  # Redirect stderr as well


def update_terminal():
    while not q.empty():  # Ensure there's something to read
        text = q.get()
        terminal.config(state=tk.NORMAL)
        terminal.insert(tk.END, text)
        terminal.yview(tk.END)
        terminal.config(state=tk.DISABLED)
    root.after(100, update_terminal)  # Check again in 100ms


root.after(100, update_terminal)
root.mainloop()
