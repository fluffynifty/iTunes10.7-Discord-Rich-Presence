# iTunes Discord RPC for old macOS

Show **"Listening to iTunes"** on Discord from a Mac that can't run Discord (OS X 10.7 Lion).

A tiny script on the Mac reads iTunes and sends it over your LAN to a Windows PC, which sets Discord Rich Presence for you.

```
 Mac (iTunes)                       Windows PC (Discord)
┌──────────────────┐   HTTP/JSON   ┌────────────────────┐
│ lion_sender.py   │ ────────────► │ win_bridge.py      │ ──► Discord
│ AppleScript poll │   LAN, :5055  │ pypresence+Spotify │
└──────────────────┘               └────────────────────┘
```

## Features

- "Listening to iTunes" activity with track, artist, album (on hover)
- Live progress bar (start/end time), follows seeking
- **Open on Spotify** button linking to the exact track (falls back to a Spotify search link)
- Cleared on pause / when iTunes quits
- Mac side is stdlib-only Python 2.7 (built into Lion), autostart via LaunchAgent

## Requirements

- **Mac:** OS X 10.7+ with iTunes and the system Python 2.7 (`/usr/bin/python`)
- **Windows PC:** Python 3.8+, Discord desktop app, same network as the Mac

## Setup

### 1. Discord application (once)

1. Go to <https://discord.com/developers/applications> → **New Application**. Name it **`iTunes`** - this name is what appears after "Listening to".
2. Copy the **Application ID**.
3. **Rich Presence → Art Assets**: upload an image and name it `itunes`.

### 2. Spotify keys (optional, for exact track links)

Skip this to get a Spotify *search* link instead.

1. <https://developer.spotify.com/dashboard> → **Create app**. Redirect URI: `http://127.0.0.1:8888/callback` (required but unused). Select **Web API**.
2. In the app's **Settings** copy the **Client ID** and **Client secret**.

### 3. Windows PC

```
cd windows
pip install -r requirements.txt
copy config.example.json config.json
```

Edit `config.json` (see table below), then run `start_bridge.bat`. Allow Python through the firewall for port 5055 when asked.

To start with Windows, put a shortcut to `start_bridge.bat` in `shell:startup`.

### 4. Mac

Edit `mac/config.json` - set `bridge_url` to your PC's LAN IP, then:

```
cd mac
./install.sh
```

This installs a LaunchAgent: the sender starts at login and is restarted if it dies. Remove it with `./uninstall.sh`. To test without installing: `python lion_sender.py`.

> After editing `config.json` or `lion_sender.py`, run `./install.sh` again to restart the sender.

## Configuration

**`windows/config.json`**

| Key                                          | Meaning                                                                |
| -------------------------------------------- | ---------------------------------------------------------------------- |
| `discord_client_id`                          | Discord Application ID                                                 |
| `spotify_client_id`, `spotify_client_secret` | Optional. Empty = search link instead of exact link                    |
| `port`                                       | Port to listen on (default `5055`)                                     |
| `token`                                      | Optional shared secret; must match the Mac's `token`. Empty = no check |
| `large_image`                                | Name of the art asset (default `itunes`)                               |

**`mac/config.json`**

| Key | Meaning |
|---|---|
| `bridge_url` | `http://<PC-IP>:<port>/` |
| `poll_seconds` | How often iTunes is checked (default `3`) |
| `token` | Same shared secret as on the PC |
