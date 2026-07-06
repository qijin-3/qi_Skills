#!/usr/bin/env bash
# status.sh — show both processes, auto-shutdown countdown, and active routes.
set -euo pipefail
source "$(dirname "$0")/lib.sh"

ts_init_state

echo "tunnel-serve status"
echo "──────────────────"

if ts_serve_running; then
  echo "router:    ✅ serve.py running (pid $(cat "$TS_SERVE_PID"))  http://127.0.0.1:${TS_PORT}"
else
  echo "router:    ⏹ serve.py not running"
fi

if ts_cf_running; then
  echo "tunnel:    ✅ cloudflared running (pid $(cat "$TS_CF_PID"))  → $TS_DOMAIN"
else
  echo "tunnel:    ⏹ cloudflared not running"
fi

if [ -f "$TS_CF_CONFIG" ]; then
  echo "config:    $TS_CF_CONFIG"
else
  echo "config:    ⚠ not set up (run scripts/bootstrap.sh)"
fi

# deadline / countdown
if [ -f "$TS_DEADLINE" ]; then
  RAW="$(tr -d '[:space:]' < "$TS_DEADLINE")"
  if [ "$RAW" = "NEVER" ]; then
    echo "auto-off:  ♾ never (until manual close)"
  elif [ -n "$RAW" ]; then
    NOW="$(date +%s)"
    if [ "$RAW" -le "$NOW" ] 2>/dev/null; then
      echo "auto-off:  ⏰ expired (will stop on next watchdog tick)"
    else
      REMAIN=$(( RAW - NOW ))
      echo "auto-off:  ⏰ in $(( REMAIN / 60 ))m$(( REMAIN % 60 ))s"
    fi
  fi
else
  echo "auto-off:  (default 1h on next start)"
fi

echo
echo "active routes:"
COUNT=0
while IFS=$'\t' read -r slug path; do
  [ -n "$slug" ] || continue
  COUNT=$((COUNT+1))
  if [ -d "$path" ]; then kind="📁 folder"
  elif [ -f "$path" ]; then kind="📄 file"
  else kind="⚠️ missing"; fi
  echo "  /${slug}/  ${kind}  →  ${path}"
  echo "       https://${TS_DOMAIN}/${slug}/"
done < <(ts_registry_list)
[ "$COUNT" -eq 0 ] && echo "  (none)"
