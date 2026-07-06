#!/usr/bin/env bash
# Common helpers for tunnel-serve scripts.
# Sourced by other scripts: `source "$(dirname "$0")/lib.sh"`

# --- Paths -----------------------------------------------------------------
TS_SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TS_CONFIG_FILE="$TS_SKILL_DIR/config.env"
TS_STATE_DIR="$TS_SKILL_DIR/state"
TS_SERVE_PY="$TS_SKILL_DIR/scripts/serve.py"
TS_REGISTRY="$TS_STATE_DIR/registry.json"
TS_SERVE_PID="$TS_STATE_DIR/serve.pid"
TS_CF_PID="$TS_STATE_DIR/cloudflared.pid"
TS_DEADLINE="$TS_STATE_DIR/deadline.txt"
TS_LOG="$TS_STATE_DIR/server.log"
TS_CF_LOG="$TS_STATE_DIR/cloudflared.log"

# --- Config (loaded from config.env) ---------------------------------------
# Required: TS_ZONE, TS_SUBDOMAIN, TS_TUNNEL_NAME
# Derived:  TS_DOMAIN = ${TS_SUBDOMAIN}.${TS_ZONE}
# Optional: TS_PORT, TS_DEFAULT_TTL, TS_CF_HOME, TS_CF_CONFIG

ts_load_config() {
  if [ -f "$TS_CONFIG_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    source "$TS_CONFIG_FILE"
    set +a
  fi

  TS_CF_HOME="${TS_CF_HOME:-${HOME}/.cloudflared}"
  TS_CF_CONFIG="${TS_CF_CONFIG:-${TS_CF_HOME}/config.yml}"
  TS_PORT="${TS_PORT:-8787}"
  TS_DEFAULT_TTL="${TS_DEFAULT_TTL:-3600}"

  if [ -n "${TS_ZONE:-}" ] && [ -n "${TS_SUBDOMAIN:-}" ]; then
    TS_DOMAIN="${TS_SUBDOMAIN}.${TS_ZONE}"
  else
    TS_DOMAIN="${TS_DOMAIN:-}"
  fi
}

# Echo missing required config keys (one per line); empty if complete.
ts_config_missing_keys() {
  ts_load_config
  [ -z "${TS_ZONE:-}" ] && echo TS_ZONE
  [ -z "${TS_SUBDOMAIN:-}" ] && echo TS_SUBDOMAIN
  [ -z "${TS_TUNNEL_NAME:-}" ] && echo TS_TUNNEL_NAME
}

# Exit with guidance when config.env is missing or incomplete.
ts_require_config() {
  if [ ! -f "$TS_CONFIG_FILE" ]; then
    ts_die_config_help "config.env 不存在"
  fi
  local missing key
  missing="$(ts_config_missing_keys)"
  if [ -n "$missing" ]; then
    ts_die_config_help "config.env 缺少必填项: $(echo "$missing" | tr '\n' ' ')"
  fi
}

# Print config error + how to fix; then exit 1.
ts_die_config_help() {
  local reason="${1:-配置无效}"
  echo "✗ $reason" >&2
  echo >&2
  echo "tunnel-serve 需要 config.env（每台机器一份，不入库）。" >&2
  echo "必填变量：TS_ZONE、TS_SUBDOMAIN、TS_TUNNEL_NAME" >&2
  echo >&2
  echo "快速创建：" >&2
  echo "  bash scripts/init-config.sh" >&2
  echo "或：" >&2
  echo "  cp config.env.example config.env   # 编辑后保存" >&2
  echo >&2
  echo "各变量含义与获取方式 → references/config-variables.md" >&2
  exit 1
}

ts_init_state() {
  mkdir -p "$TS_STATE_DIR"
  [ -f "$TS_REGISTRY" ] || echo '{}' > "$TS_REGISTRY"
}

# --- Slug ------------------------------------------------------------------
# Clean a name into a URL-safe slug: lowercase, [a-z0-9-] only, trim/dedupe
# dashes, max 63 chars.
ts_make_slug() {
  local name base
  name="$1"
  base="$(basename "$name")"
  base="${base%.*}"
  [ -z "$base" ] && base="$(basename "$name")"
  echo "$base" \
    | tr '[:upper:]' '[:lower:]' \
    | tr -c 'a-z0-9-' '-' \
    | sed 's/--*/-/g' \
    | sed 's/^-//; s/-$//' \
    | cut -c1-63
}

# --- Process liveness ------------------------------------------------------
# Echo PID if a pidfile points to a live process; empty otherwise.
ts_check_pidfile() {
  local pidfile="$1" pid
  [ -f "$pidfile" ] || return 0
  pid="$(cat "$pidfile" 2>/dev/null)"
  [ -n "$pid" ] || return 0
  if kill -0 "$pid" 2>/dev/null; then
    echo "$pid"
  fi
  return 0
}

ts_serve_pid() { ts_check_pidfile "$TS_SERVE_PID"; }
ts_cf_pid()    { ts_check_pidfile "$TS_CF_PID"; }

ts_serve_running() { [ -n "$(ts_serve_pid)" ]; }
ts_cf_running()    { [ -n "$(ts_cf_pid)" ]; }

# --- Registry --------------------------------------------------------------
ts_registry_list() {
  ts_init_state
  python3 - "$TS_REGISTRY" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    d = {}
for slug, entry in d.items():
    path = entry.get("path") if isinstance(entry, dict) else entry
    print(f"{slug}\t{path}")
PY
}

ts_registry_set() {
  local slug="$1" path="$2"
  python3 - "$TS_REGISTRY" "$slug" "$path" <<'PY'
import json, sys, time, os
reg_path, slug, path = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    d = json.load(open(reg_path))
except Exception:
    d = {}
d[slug] = {"path": os.path.abspath(path), "added": int(time.time())}
json.dump(d, open(reg_path, "w"), indent=2, ensure_ascii=False)
PY
}

ts_registry_del() {
  local slug="$1"
  python3 - "$TS_REGISTRY" "$slug" <<'PY'
import json, sys
reg_path, slug = sys.argv[1], sys.argv[2]
try:
    d = json.load(open(reg_path))
except Exception:
    d = {}
if slug in d:
    del d[slug]
    json.dump(d, open(reg_path, "w"), indent=2, ensure_ascii=False)
    sys.exit(0)
sys.exit(1)
PY
}

ts_registry_count() {
  python3 - "$TS_REGISTRY" <<'PY'
import json, sys
try:
    print(len(json.load(open(sys.argv[1]))))
except Exception:
    print(0)
PY
}

# --- Prerequisites ---------------------------------------------------------
ts_have() { command -v "$1" >/dev/null 2>&1; }

ts_check_bootstrap() {
  ts_require_config
  if [ ! -f "$TS_CF_CONFIG" ]; then
    ts_die "tunnel 尚未初始化。运行: bash scripts/bootstrap.sh"
  fi
  ts_have cloudflared || ts_die "未找到 cloudflared。运行 bootstrap 或: brew install cloudflared"
}

# --- Start / stop ----------------------------------------------------------
# Start serve.py (router) in the background if not running.
ts_start_serve() {
  if ts_serve_running; then return 0; fi
  rm -f "$TS_SERVE_PID"
  TS_PORT="$TS_PORT" nohup python3 "$TS_SERVE_PY" >> "$TS_LOG" 2>&1 &
  echo $! > "$TS_SERVE_PID"
  local i
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if curl -fsS -o /dev/null "http://127.0.0.1:${TS_PORT}/" 2>/dev/null; then
      return 0
    fi
    sleep 0.3
  done
  return 0
}

# Start cloudflared tunnel in the background if not running.
ts_start_cf() {
  if ts_cf_running; then return 0; fi
  rm -f "$TS_CF_PID"
  nohup cloudflared tunnel --config "$TS_CF_CONFIG" run "$TS_TUNNEL_NAME" \
    >> "$TS_CF_LOG" 2>&1 &
  echo $! > "$TS_CF_PID"
  sleep 1
  return 0
}

# Start the whole stack (both processes). Sets default deadline if none.
ts_start_stack() {
  ts_check_bootstrap
  ts_start_serve
  ts_start_cf
  [ -f "$TS_DEADLINE" ] || echo $(( $(date +%s) + TS_DEFAULT_TTL )) > "$TS_DEADLINE"
}

ts_kill_pidfile() {
  local pidfile="$1" pid
  pid="$(ts_check_pidfile "$pidfile")" || true
  [ -n "$pid" ] || { rm -f "$pidfile"; return 0; }
  kill "$pid" 2>/dev/null || true
  local i
  for i in 1 2 3 4 5; do
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.3
  done
  kill -9 "$pid" 2>/dev/null || true
  rm -f "$pidfile"
}

ts_stop_serve() { ts_kill_pidfile "$TS_SERVE_PID"; }
ts_stop_cf()    { ts_kill_pidfile "$TS_CF_PID"; }

ts_stop_stack() {
  ts_stop_cf
  ts_stop_serve
}

ts_die() {
  echo "✗ $*" >&2
  exit 1
}

# Load config as soon as lib.sh is sourced.
ts_load_config
