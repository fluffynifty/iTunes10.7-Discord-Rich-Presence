#!/bin/bash
PLIST="$HOME/Library/LaunchAgents/com.itunesrpc.sender.plist"
launchctl unload "$PLIST" 2>/dev/null
rm -f "$PLIST"
echo "Removed."
