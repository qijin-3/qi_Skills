#!/usr/bin/env bash
# expose.sh <file-or-folder> [custom-slug]
# Register a route, starting the router server AND cloudflared if needed.
set -euo pipefail
source "$(dirname "$0")/lib.sh"

[ $# -ge 1 ] || ts_die "usage: expose.sh <file-or-folder> [custom-slug]"

TARGET="$1"
[ -e "$TARGET" ] || ts_die "path does not exist: $TARGET"

ABS="$(cd "$(dirname "$TARGET")" && pwd)/$(basename "$TARGET")"

if [ $# -ge 2 ]; then
  SLUG="$2"
  if ! printf '%s' "$SLUG" | grep -Eq '^[a-z0-9-]{1,63}$'; then
    ts_die "custom slug must be 1-63 chars of [a-z0-9-]: '$SLUG'"
  fi
else
  SLUG="$(ts_make_slug "$TARGET")"
  [ -n "$SLUG" ] || ts_die "could not derive a slug from '$TARGET'; pass one explicitly"
fi

ts_init_state

# Start the whole stack (serve.py + cloudflared) if not running.
ts_start_stack

# Register the route
ts_registry_set "$SLUG" "$ABS"

URL="https://${TS_DOMAIN}/${SLUG}/"
echo "✅ ${URL}"
if [ -f "$ABS" ]; then
  echo "   └ direct view: ${URL}"
fi
echo "   (local: http://127.0.0.1:${TS_PORT}/${SLUG}/)"
echo "   (tunnel may need a few seconds to register on first start)"
