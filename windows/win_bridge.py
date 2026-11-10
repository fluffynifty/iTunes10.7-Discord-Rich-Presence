import json, time, base64, os, sys, urllib.request, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pypresence import Presence, ActivityType

HERE = os.path.dirname(os.path.abspath(__file__))
try:
    cfg = json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8"))
except FileNotFoundError:
    sys.exit("config.json not found - copy config.example.json to config.json and fill it in.")

CLIENT_ID = cfg["discord_client_id"]
SPOTIFY_ID = cfg.get("spotify_client_id", "")
SPOTIFY_SECRET = cfg.get("spotify_client_secret", "")
PORT = cfg.get("port", 5055)
TOKEN = cfg.get("token", "")
IMAGE = cfg.get("large_image", "itunes")

rpc = None
_tok = {"v": None, "exp": 0}
_cache = {}

def connect():
    """One connection attempt. Returns True on success."""
    global rpc
    try:
        rpc = Presence(CLIENT_ID)
        rpc.connect()
        print("connected to Discord")
        return True
    except Exception as e:
        rpc = None
        print("Discord not available:", e)
        return False

def token():
    if _tok["v"] and time.time() < _tok["exp"]:
        return _tok["v"]
    auth = base64.b64encode(f"{SPOTIFY_ID}:{SPOTIFY_SECRET}".encode()).decode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=b"grant_type=client_credentials",
        headers={"Authorization": "Basic " + auth})
    r = json.load(urllib.request.urlopen(req, timeout=5))
    _tok["v"] = r["access_token"]
    _tok["exp"] = time.time() + r["expires_in"] - 60
    return _tok["v"]

def spotify_url(title, artist):
    key = (title, artist)
    if key in _cache:
        return _cache[key]
    url = "https://open.spotify.com/search/" + urllib.parse.quote(f"{artist} {title}")
    if SPOTIFY_ID and SPOTIFY_SECRET:
        try:
            q = urllib.parse.urlencode({"q": f"track:{title} artist:{artist}",
                                        "type": "track", "limit": 1})
            req = urllib.request.Request("https://api.spotify.com/v1/search?" + q,
                                         headers={"Authorization": "Bearer " + token()})
            items = json.load(urllib.request.urlopen(req, timeout=5))["tracks"]["items"]
            if items:
                url = items[0]["external_urls"]["spotify"]
        except Exception as e:
            print("spotify lookup failed:", e)
    _cache[key] = url
    return url

def apply(d):
    if rpc is None:
        raise RuntimeError("not connected")
    if d.get("state") == "playing":
        start = int(time.time()) - d["pos"]
        rpc.update(
            activity_type=ActivityType.LISTENING,
            details=d["title"][:128],
            state=d["artist"][:128],
            large_image=IMAGE,
            large_text=d["album"][:128],
            start=start,
            end=start + d["dur"],
            buttons=[{"label": "Open on Spotify",
                      "url": spotify_url(d["title"], d["artist"])[:512]}],
        )
    else:
        rpc.clear()

class H(BaseHTTPRequestHandler):
    def reply(self, code):
        self.send_response(code)
        self.end_headers()
        self.wfile.write(b"ok" if code == 200 else b"error")

    def do_POST(self):
        if TOKEN and self.headers.get("X-Token") != TOKEN:
            return self.reply(403)
        try:
            n = int(self.headers.get("Content-Length", 0))
            d = json.loads(self.rfile.read(n))
        except Exception:
            return self.reply(400)
        try:
            apply(d)
        except Exception as e:
            print("rpc error, reconnecting:", e)
            if not connect():
                return self.reply(503)   # Mac keeps retrying
            try:
                apply(d)
            except Exception as e2:
                print("rpc error:", e2)
                return self.reply(503)
        self.reply(200)

    def log_message(self, *a):
        pass

connect()
print(f"listening on port {PORT}")
HTTPServer(("0.0.0.0", PORT), H).serve_forever()
