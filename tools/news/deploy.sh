#!/bin/bash
# Install the weekly news check outside Dropbox and (re)load its launchd job.
# Run by hand after editing anything in tools/news/:  bash tools/news/deploy.sh
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/.local/share/aurora_news"
PLIST="$HOME/Library/LaunchAgents/com.sfseiji.aurora-news-weekly.plist"
mkdir -p "$DEST" "$HOME/Library/Logs"
for f in sweep.py weekly_check.py apply_cards.py state_tool.py; do
  cp "$SRC/$f" "$DEST/$f"
done
sed "s#__HOME__#$HOME#g" "$SRC/com.sfseiji.aurora-news-weekly.plist" > "$PLIST"
plutil -lint "$PLIST" >/dev/null
launchctl bootout "gui/$(id -u)/com.sfseiji.aurora-news-weekly" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "deployed to $DEST; launchd job loaded:"
launchctl print "gui/$(id -u)/com.sfseiji.aurora-news-weekly" | grep -E "state|path =|last exit" | head -5
