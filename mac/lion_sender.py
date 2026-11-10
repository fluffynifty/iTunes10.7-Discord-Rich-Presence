#!/usr/bin/python
import subprocess, json, time, urllib2, os

HERE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(HERE, "config.json")))
BRIDGE = cfg["bridge_url"]
POLL = cfg.get("poll_seconds", 3)
TOKEN = cfg.get("token", "")

SCRIPT = '''
tell application "System Events" to set r to (name of processes) contains "iTunes"
if not r then return "stopped"
tell application "iTunes"
    if player state is not playing then return "paused"
    set t to current track
    return "playing" & tab & (name of t) & tab & (artist of t) & tab & (album of t) & tab & ((player position) as integer) & tab & ((duration of t) as integer)
end tell
'''

def get_state():
    p = subprocess.Popen(["osascript", "-e", SCRIPT],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = p.communicate()[0].strip().decode("utf-8", "ignore")
    parts = out.split("\t")
    if parts[0] != "playing" or len(parts) < 6:
        return {"state": parts[0] or "stopped"}
    return {"state": "playing", "title": parts[1], "artist": parts[2],
            "album": parts[3], "pos": int(parts[4]), "dur": int(parts[5])}

def send(data):
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["X-Token"] = TOKEN
    req = urllib2.Request(BRIDGE, json.dumps(data), headers)
    urllib2.urlopen(req, timeout=5).read()

sent_key = None
prev = None
while True:
    try:
        s = get_state()
        key = (s.get("state"), s.get("title"), s.get("artist"))
        jumped = (prev is not None and s.get("pos") is not None
                  and prev.get("pos") is not None
                  and abs((s["pos"] - prev["pos"]) - POLL) > 3)
        if key != sent_key or jumped:
            send(s)
            sent_key = key
        prev = s
    except Exception as e:
        print("error: %s" % e)
    time.sleep(POLL)
