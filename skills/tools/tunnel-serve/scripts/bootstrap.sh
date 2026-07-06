#!/usr/bin/env bash
# bootstrap.sh — one-time setup for the local "share" Cloudflare Tunnel.
#
# Steps:
#   1. ensure cloudflared is installed (brew)
#   2. ensure logged in (cloudflared tunnel login) — opens browser, you pick jinqi33.top
#   3. create tunnel named "share" (if missing) -> writes ~/.cloudflared/share.json
#   4. write ~/.cloudflared/config.yml with ingress: share.jinqi33.top -> 127.0.0.1:8787
#   5. create DNS CNAME: share.jinqi33.top -> <tunnel-id>.cfargotunnel.com
#
# Idempotent: safe to re-run; skips steps already done.
set -euo pipefail
source "$(dirname "$0")/lib.sh"

echo "═══ tunnel-serve bootstrap ═══"
echo

# --- 1. cloudflared binary -------------------------------------------------
if ts_have cloudflared; then
  echo "✓ cloudflared found: $(command -v cloudflared)"
else
  echo "· cloudflared not found. Installing via Homebrew..."
  if ! ts_have brew; then
    ts_die "Homebrew not found. Install cloudflared manually, then re-run."
  fi
  brew install cloudflared
  ts_have cloudflared || ts_die "cloudflared install failed"
  echo "✓ cloudflared installed"
fi
echo

# --- 2. login (cert.pem) ---------------------------------------------------
if [ -f "${TS_CF_HOME}/cert.pem" ]; then
  echo "✓ already logged in (cert.pem present)"
else
  echo "→ Opening browser for cloudflared tunnel login..."
  echo "  In the browser, select the zone: jinqi33.top"
  echo "  Authorize, then return here."
  echo
  cloudflared tunnel login
  [ -f "${TS_CF_HOME}/cert.pem" ] || ts_die "login did not produce cert.pem — did you authorize jinqi33.top?"
  echo "✓ logged in"
fi
echo

# --- 3. create tunnel ------------------------------------------------------
mkdir -p "$TS_CF_HOME"
# Resolve the tunnel UUID by listing existing tunnels first.
# cloudflared stores credentials as <UUID>.json (not <name>.json), so we must
# learn the UUID before we can know the credentials path.
TUNNEL_ID="$(cloudflared tunnel list 2>/dev/null | awk -v n="$TS_TUNNEL_NAME" '$2==n{print $1; exit}')"
if [ -n "$TUNNEL_ID" ]; then
  echo "✓ tunnel '$TS_TUNNEL_NAME' already exists (id $TUNNEL_ID)"
else
  echo "→ Creating tunnel '$TS_TUNNEL_NAME'..."
  (cd "$TS_CF_HOME" && cloudflared tunnel create "$TS_TUNNEL_NAME")
  TUNNEL_ID="$(cloudflared tunnel list 2>/dev/null | awk -v n="$TS_TUNNEL_NAME" '$2==n{print $1; exit}')"
  [ -n "$TUNNEL_ID" ] || ts_die "tunnel create did not produce a resolvable id"
  echo "✓ tunnel created"
fi
# The real credentials file is named by UUID, not by tunnel name.
TUNNEL_CRED="${TS_CF_HOME}/${TUNNEL_ID}.json"
if [ ! -f "$TUNNEL_CRED" ]; then
  # fall back to any TunnelID match inside the json files (extremely unlikely path)
  for jf in "$TS_CF_HOME"/*.json; do
    [ -f "$jf" ] || continue
    id_in_file="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("TunnelID",""))' "$jf" 2>/dev/null || true)"
    if [ "$id_in_file" = "$TUNNEL_ID" ]; then TUNNEL_CRED="$jf"; break; fi
  done
fi
[ -f "$TUNNEL_CRED" ] || ts_die "credentials file not found for tunnel $TUNNEL_ID (expected $TUNNEL_CRED)"
echo "  tunnel id: $TUNNEL_ID"
echo "  credentials: $TUNNEL_CRED"
echo

# --- 4. write config.yml ---------------------------------------------------
# Ingress: the share hostname -> local router; catch-all -> 404.
echo "→ Writing $TS_CF_CONFIG ..."
cat > "$TS_CF_CONFIG" <<EOF
tunnel: $TUNNEL_ID
credentials-file: $TUNNEL_CRED

ingress:
  - hostname: $TS_DOMAIN
    service: http://127.0.0.1:${TS_PORT}
  - service: http_status:404
EOF
echo "✓ config written"
echo

# --- 5. DNS route ----------------------------------------------------------
echo "→ Ensuring DNS route $TS_DOMAIN -> ${TUNNEL_ID}.cfargotunnel.com ..."
# `tunnel route dns` is idempotent; if the CNAME exists it errors harmlessly.
cloudflared tunnel route dns "$TS_TUNNEL_NAME" "$TS_DOMAIN" 2>&1 || \
  echo "  (if it said the record already exists, that's fine)"
echo "✓ DNS route ensured"
echo

echo "═══ Setup complete ═══"
echo
echo "Next: expose something, e.g.:"
echo "  bash scripts/expose.sh /path/to/your.html"
echo "  → https://$TS_DOMAIN/<slug>/"
echo
echo "To verify connectivity before exposing content, see references/setup-guide.md."
