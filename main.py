import tkinter as tk
from tkinter import ttk
import webbrowser
import os
from process_youtube_link import inspect_link

# Create the main application window
root = tk.Tk()
root.title("Vaporwave UI")
root.geometry("800x500")  # Adjusted window size
root.configure(bg='#0d0221')  # Dark neon background

# Make columns expandable for centering
root.columnconfigure(0, weight=1)

# Define colors
neon_pink = "#ff007f"
neon_blue = "#00eaff"
neon_purple = "#9d00ff"

# Create a custom style
style = ttk.Style()
style.configure("TButton", font=("Helvetica", 12, "bold"), foreground=neon_pink, padding=10)
style.map("TButton", background=[("active", neon_purple)])

# Function to open a URL search tool
def open_search():
    webbrowser.open("https://music.youtube.com/")

# Function to open the downloads folder
def open_downloads():
    desktop = os.path.expanduser("~")
    destination_folder = os.path.join(desktop, "Desktop", "metadata_filler", "music")
    os.startfile(destination_folder) if os.path.exists(destination_folder) else print("Folder does not exist.")

# Function to handle YouTube link
def open_youtube():
    url = yt_link.get()
    if url:
        inspect_link(url)  # Call actual function
        print('Download Complete')

# Create UI elements
label = tk.Label(root, text="VAPORWAVE UI", fg=neon_blue, bg="#0d0221", font=("Helvetica", 20, "bold"))
label.grid(row=0, column=0, pady=10, sticky="n")

# Input for YouTube link
yt_link = tk.Entry(root, width=50)
yt_link.grid(row=1, column=0, pady=5, padx=20, sticky="ew")

yt_button = ttk.Button(root, text="Download YouTube Link", style="TButton", command=open_youtube)
yt_button.grid(row=2, column=0, pady=10, padx=20, sticky="ew")

# Create buttons for "Home", "Search", and "Downloads"
buttons = [
    ("Home", None), 
    ("Search", open_search), 
    ("Downloads", open_downloads)
]

for idx, (btn_text, command) in enumerate(buttons, start=3):
    button = ttk.Button(root, text=btn_text, style="TButton", command=command)
    button.grid(row=idx, column=0, pady=5, padx=20, sticky="ew")

# Run the application
root.mainloop()
