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

# VRChat OSC settings
VRCHAT_IP = "127.0.0.1"
VRCHAT_PORT_SEND = 9000
client = SimpleUDPClient(VRCHAT_IP, VRCHAT_PORT_SEND)

# Spotify API auth
scope = "user-read-playback-state"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    scope=scope,
    client_id=os.getenv("client_id"),
    client_secret=os.getenv("client_secret"),
    redirect_uri=os.getenv("redirect_uri")
))

update_lock = threading.Lock()
last_track = ""
auto_update = True
pause_until = 0
typing_timer = None
is_typing = False

root = tk.Tk()
root.title("VRChat Spotify OSC")
root.geometry("700x400")

def log(message):
    log_widget.configure(state='normal')
    log_widget.insert(tk.END, message + "\n")
    log_widget.see(tk.END)
    log_widget.configure(state='disabled')

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

# Start the spotify update thread before the GUI mainloop
threading.Thread(target=spotify_update_loop, daemon=True).start()


#region Left frame: Log, Spotify info, chat input
left_frame = ttk.Frame(root, padding=10)
left_frame.pack(side='left', fill='both', expand=True)

# Right frame: Controls
right_frame = ttk.Frame(root, padding=10)
right_frame.pack(side='right', fill='y')

# Log widget (scrollable)
log_widget = ScrolledText(left_frame, state='disabled', height=20, width=60)
log_widget.pack(fill='both', expand=True)

# Spotify info label
spotify_info = ttk.Label(left_frame, text="No track playing", font=("Helvetica", 12, "bold"))
spotify_info.pack(pady=(5, 10))

# Chat input frame inside left_frame
chat_frame = ttk.Frame(left_frame)
chat_frame.pack(fill='x')

chat_entry = ttk.Entry(chat_frame)
chat_entry.pack(side='left', fill='x', expand=True)
chat_entry.bind("<Return>", lambda event: on_send_click())
chat_entry.bind("<Key>", lambda event: on_keypress(event))

send_button = ttk.Button(chat_frame, text="Send", command=on_send_click)
send_button.pack(side='left', padx=(5, 0))

#endregion

#region Right frame : Controls
send_track_button = ttk.Button(right_frame, text="Send Current Track", command=send_spotify_track)
send_track_button.pack(pady=5, fill='x')

clear_log_button = ttk.Button(right_frame, text="Clear Log")
clear_log_button.pack(pady=5, fill='x')

# --- Start GUI ---
root.mainloop()