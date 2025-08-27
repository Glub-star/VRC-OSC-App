# VRChat Spotify OSC Dashboard

A Python-based desktop app that allows you to send your currently playing Spotify track (or custom messages) to VRChat via OSC. It also features a log, a chat input box, and a theme selector.

---
## You can send ";" to send current track



## HOW TO SETUP

To use the app, you need Spotify API credentials. Follow these steps:

1. **Sign in to Spotify Developer Dashboard:**
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications).
   - Log in with your Spotify account.

2. **Create a New App:**
   - Click **“Create an App”**.
   - Enter a name and description for your app.
   - Click **“Create”**.

3. **Copy Credentials:**
   - After creating the app, you’ll see your **Client ID** and **Client Secret**.
   - Keep them safe; you’ll need them in the app.

4. **Set Redirect URI:**
   - Click **Edit Settings** on your app page.
   - Under **Redirect URIs**, add:  
     ```
     http://localhost:8888/callback
     ```
   - Click **Save**.

5. **Enter Credentials in the App:**
   - Run the app (`python main.py`).
   - If `.env` file or credentials are missing, a popup will appear.
   - Enter your **Client ID**, **Client Secret**, and **Redirect URI**.
   - Click **Save**. This creates a `.env` file automatically.

6. **Restart the App:**
   - Close and relaunch the app to load the credentials.

---

> ⚠️ Make sure Spotify is running and playing a track for the app to detect and send updates.


---

## Features

- Sends currently playing Spotify track to VRChat chat.
- Sends typing indicators to VRChat.
- Pauses automatic updates when typing messages.
- Light and dark theme support.
- Auto-detects missing Spotify API credentials and allows setup via a GUI popup.
- Logs all messages and Spotify updates in a scrollable log window.

---

## Screenshots

**Main Dashboard**

<img width="905" height="537" alt="image" src="https://github.com/user-attachments/assets/97c99f8b-023c-4633-a3ad-ef4ec39b0725" />

**Environment Setup Popup**

<img width="412" height="289" alt="image" src="https://github.com/user-attachments/assets/38bf0e33-2350-45a3-a43e-ed61d6e11737" />


---

## Requirements

- Python 3.10+
- Packages:
  ```bash
  pip install spotipy python-osc python-dotenv
