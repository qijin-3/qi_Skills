#!/usr/bin/env bash
# extend.sh <minutes>
#   Set the auto-shutdown deadline to <minutes> from now.
#   extend.sh 0  -> never auto-shut (until manual close)
set -euo pipefail
source "$(dirname "$0")/lib.sh"

[ $# -ge 1 ] || ts_die "usage: extend.sh <minutes>  (0 = never auto-shut)"

MIN="$1"
case "$MIN" in
  ''|*[!0-9]*) ts_die "minutes must be a non-negative integer (got '$MIN')" ;;
esac

ts_init_state

if [ "$MIN" -eq 0 ]; then
  echo "NEVER" > "$TS_DEADLINE"
  echo "✓ auto-shutdown disabled (server runs until you close it)"
else
  NOW="$(date +%s)"
  echo $(( NOW + MIN * 60 )) > "$TS_DEADLINE"
  echo "✓ auto-shutdown set to ${MIN} minutes from now"
fi

# The running server picks up the new deadline within a few seconds (watchdog
# polls state/deadline.txt every 5s). No restart needed.
if ts_serve_running; then
  echo "  (running server will adopt this within ~5s)"
fi
