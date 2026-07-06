#!/usr/bin/env bash
# close.sh [slug]
#   with a slug: remove just that route.
#                If no routes remain, also stop the whole stack.
#   no slug:     stop cloudflared + serve.py and clear all routes.
set -euo pipefail
source "$(dirname "$0")/lib.sh"

ts_init_state

if [ $# -ge 1 ]; then
  SLUG="$1"
  if ts_registry_del "$SLUG"; then
    echo "✓ removed route '$SLUG'"
  else
    ts_die "no such route: '$SLUG'"
  fi
  # If no routes remain, shut the stack down (nothing left to serve).
  if [ "$(ts_registry_count)" -eq 0 ]; then
    if ts_cf_running || ts_serve_running; then
      ts_stop_stack
      echo "· no routes remain, stopped tunnel-serve"
    fi
  fi
  exit 0
fi

# No slug -> full shutdown
ts_stop_stack
echo '{}' > "$TS_REGISTRY"
rm -f "$TS_DEADLINE"
echo "✓ stopped tunnel-serve and cleared all routes"
