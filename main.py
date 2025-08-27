import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from pythonosc.udp_client import SimpleUDPClient
import threading
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
from dotenv import load_dotenv
import os
import sys

# VRChat OSC settings
VRCHAT_IP = "127.0.0.1"
VRCHAT_PORT_SEND = 9000
client = SimpleUDPClient(VRCHAT_IP, VRCHAT_PORT_SEND)
load_dotenv()  # make sure .env values are loaded into the environment

# Spotify API auth
scope = "user-read-playback-state"

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

missing = []
update_lock = threading.Lock()
last_track = ""
auto_update = True
pause_until = 0
typing_timer = None
is_typing = False
log_widget = None

THEMES = {
    'light': {
        'bg': 'white',
        'fg': 'black',
        'button_bg': '#eee',
        'button_fg': '#000',
        'font': ('Helvetica', 12)
    },
    'dark': {
        'bg': '#222222',
        'fg': 'white',
        'button_bg': '#444',
        'button_fg': 'white',
        'font': ('Helvetica', 12)
    }
}


root = tk.Tk()
root.title("VRChat Spotify OSC")
root.geometry("900x500")
theme_var = tk.StringVar(value='light')
style = ttk.Style()
style.configure('Custom.TButton',
                background=THEMES[theme_var.get()]['button_bg'],
                foreground=THEMES[theme_var.get()]['button_fg'])

#region sub-processes

def restart_app():
    """Restart the current Python script."""
    python = sys.executable  # path to Python interpreter
    os.execl(python, python, *sys.argv)

# Function to show the setup popup
def show_env_setup():
    setup_window = tk.Toplevel(root)
    setup_window.title("Spotify Setup")
    setup_window.geometry("400x250")

    tk.Label(setup_window, text="Enter your Spotify API credentials:").pack(pady=10)

    entries = {}
    for var in ["CLIENT_ID", "CLIENT_SECRET", "REDIRECT_URI"]:
        frame = tk.Frame(setup_window)
        frame.pack(fill="x", pady=5, padx=10)
        tk.Label(frame, text=var, width=12, anchor="w").pack(side="left")
        entry = tk.Entry(frame, show="*" if "SECRET" in var else None, width=40)
        entry.pack(side="left", expand=True, fill="x")
        entries[var] = entry

    def save_env():
        with open(".env", "w") as f:
            for var, entry in entries.items():
                f.write(f"{var}={entry.get().strip()}\n")
        log("[INFO] Saved new .env file. Restarting the app...")
        setup_window.destroy()
        restart_app() 


    tk.Button(setup_window, text="Save", command=save_env).pack(pady=20)

#Themes
def on_theme_change(event=None):
    selected_theme = theme_var.get()
    apply_theme(selected_theme)

def apply_theme(theme_name):
    theme = THEMES[theme_name]
    root.configure(bg=theme['bg'])
    left_frame.configure(bg=theme['bg'])
    right_frame.configure(bg=theme['bg'])
    
    log_widget.configure(bg=theme['bg'], fg=theme['fg'], insertbackground=theme['fg'])
    spotify_info.configure(bg=theme['bg'], fg=theme['fg'], font=theme['font'])
    chat_entry.configure(bg=theme['bg'], fg=theme['fg'], insertbackground=theme['fg'], font=theme['font'])
    send_button.configure(bg=theme['button_bg'], fg=theme['button_fg'])
    
    style.configure('Custom.TButton',
                    background=theme['button_bg'],
                    foreground=theme['button_fg'])


# Logging
def log(message):
    if log_widget:
        log_widget.configure(state='normal')
        log_widget.insert(tk.END, message + "\n")
        log_widget.see(tk.END)
        log_widget.configure(state='disabled')
    else:
        print(message)

#Essentials
def send_message(msg):
    global auto_update, pause_until, is_typing
    msg = msg.strip()
    if not msg:
        return

    is_typing = False  # stop typing mode

    with update_lock:
        if msg == ";":
            auto_update = True
            pause_until = 0
            log("[INFO] Auto-update enabled by ';' command.")
        else:
            auto_update = False
            pause_until = time.time() + 10
            log(f"[INFO] Auto-update paused until {time.strftime('%H:%M:%S', time.localtime(pause_until))}")

    if msg == ";":
        send_spotify_track()
    else:
        client.send_message("/chatbox/input", [msg, True])
        log(f"[UI SEND] {msg}")

    chat_entry.delete(0, tk.END)

def send_typing_indicator():
    global is_typing
    if not is_typing and chat_entry.get().strip():
        is_typing = True
        client.send_message("/chatbox/input", [". . .", True])
        log("[TYPING] Sending typing indicator...")

def on_send_click():
    msg = chat_entry.get()
    send_message(msg)

def on_keypress(event):
    global typing_timer, is_typing, auto_update, pause_until

    # Cancel any old typing timer
    if typing_timer:
        root.after_cancel(typing_timer)

    # Schedule the "typing..." indicator
    typing_timer = root.after(500, send_typing_indicator)

    # Pause auto-update immediately
    auto_update = False
    pause_until = time.time() + 5  # big number so it won't auto-resume mid-typing

# --- Spotify update loop ---
def send_spotify_track():
    global last_track
    try:
        current = sp.current_playback()
        if current and current['is_playing']:
            track = current['item']['name']
            artist = current['item']['artists'][0]['name']
            spotify_info.config(text=f"{track} - {artist}")
            
            # Get progress and duration in milliseconds
            progress_ms = current['progress_ms']
            duration_ms = current['item']['duration_ms']
            
            # Convert milliseconds to MM:SS format
            progress_minutes = progress_ms // 60000
            progress_seconds = (progress_ms % 60000) // 1000
            duration_minutes = duration_ms // 60000
            duration_seconds = (duration_ms % 60000) // 1000
            
            # Format the progress string
            progress_str = f"{progress_minutes:02}:{progress_seconds:02} / {duration_minutes:02}:{duration_seconds:02}"
            
            message = f"🎵 {track} - {artist} [{progress_str}]"
            
            if message != last_track:
                # Use a lock to ensure thread safety
                with update_lock:
                    client.send_message("/chatbox/input", [message, True])
                    log(f"[SEND] {message}")
                    last_track = message
        else:
            if last_track:
                log("[SEND] No track playing or playback paused.")
                last_track = ""
                spotify_info.config(text="No track playing")
    except Exception as e:
        log(f"[ERROR] Spotify API error: {e}")

def spotify_update_loop():
    global auto_update, pause_until
    while True:
        now = time.time()
        
        can_send_spotify = False
        with update_lock:  # Acquire the lock
            # Check the state and update it if necessary
            if not auto_update and now > pause_until:
                auto_update = True
                log("[INFO] Auto-update enabled after timeout.")
            
            # Read the current state
            if auto_update:
                can_send_spotify = True
        # Lock is released here
        
        if can_send_spotify:
            send_spotify_track()
        else:
            log("[INFO] Paused sending spotify updates.")
        
        time.sleep(10)

#endregion

if not CLIENT_ID:
    missing.append("CLIENT_ID")
if not CLIENT_SECRET:
    missing.append("CLIENT_SECRET")
if not REDIRECT_URI:
    missing.append("REDIRECT_URI")

if missing:
    print(f"[ERROR] Missing environment variables: {', '.join(missing)}")
    show_env_setup()  # opens the popup to fill in credentials
    sp = None  # don’t try to create Spotify client yet
else:
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope=scope,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI
    ))

# Start the spotify update thread before the GUI mainloop
threading.Thread(target=spotify_update_loop, daemon=True).start()

#region Left frame: Log, Spotify info, chat input
left_frame = tk.Frame(root, bg=THEMES[theme_var.get()]['bg'])
left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

# Right frame: Controls
right_frame = tk.Frame(root, bg=THEMES[theme_var.get()]['bg'])
right_frame.pack(side='right', fill='y', padx=10, pady=10)
# Log widget (scrollable)
log_widget = ScrolledText(left_frame, state='disabled', height=20, width=60)
log_widget.pack(fill='both', expand=True)

# Spotify info label
spotify_info = tk.Label(left_frame, text="No track playing", font=("Helvetica", 12, "bold"))
spotify_info.pack(pady=(5, 10))

# Chat input frame inside left_frame
chat_frame = tk.Frame(left_frame)
chat_frame.pack(fill='x')

chat_entry = tk.Entry(chat_frame, bd=2, relief="solid")
chat_entry.pack(side='left', fill='x', expand=True, padx=(0, 5), pady=5)

chat_entry.bind("<Return>", lambda event: on_send_click())
chat_entry.bind("<Key>", lambda event: on_keypress(event))

send_button = tk.Button(chat_frame, text="Send", command=on_send_click)
send_button.pack(side='left', padx=(5, 0))

#endregion

#region Right frame : Controls, themes
send_track_button = ttk.Button(right_frame, text="Send Current Track", command=send_spotify_track)
send_track_button.pack(pady=5, fill='x')


clear_log_button = ttk.Button(right_frame, text="Clear Log")
clear_log_button.pack(pady=5, fill='x')

send_track_button.configure(style='Custom.TButton')
clear_log_button.configure(style='Custom.TButton')



theme_selector = ttk.Combobox(right_frame, textvariable=theme_var, values=list(THEMES.keys()), state='readonly')
theme_selector.pack(pady=10)
theme_selector.bind("<<ComboboxSelected>>", on_theme_change)

# --- Start GUI ---
apply_theme(theme_var.get())
root.mainloop()