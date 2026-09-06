#!/bin/bash
# =============================================================================
#  Amisoria host setup — run ON the Mac (mini) that hosts OpenClaw.
#
#  What it does (idempotent; safe to re-run):
#    1. Checks prerequisites: openclaw, Tailscale.app, python3.
#    2. Configures OpenClaw for the Amisoria iPhone app:
#         - gateway.bind = loopback, gateway.tailscale.mode = off (we run tailscale serve ourselves)
#         - gateway.controlUi.allowedOrigins += https://<your-magicdns>
#         - enables provider plugins: openai, anthropic, google, openrouter, ollama, microsoft
#         - compaction.reserveTokensFloor = 6000 (keeps small local models usable)
#         - tts.auto = off (the app runs its own voice pipeline)
#    3. Installs the Amisoria bridge as a launchd service (com.amisoria.bridge).
#    4. Exposes gateway + bridge through Tailscale Serve (HTTPS, tailnet-only).
#    5. Restarts the gateway and prints what to type into the iPhone app.
#
#  Usage:  bash setup-host.sh
#  Docs:   https://github.com/amisoria/amisoria
# =============================================================================
set -euo pipefail

say()  { printf "\n\033[1;36m▶ %s\033[0m\n" "$*"; }
ok()   { printf "  \033[32m✓\033[0m %s\n" "$*"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$*"; }
die()  { printf "\n\033[31m✗ %s\033[0m\n" "$*"; exit 1; }

HERE="$(cd "$(dirname "$0")" && pwd)"
OC_DIR="$HOME/.openclaw"
OC_CFG="$OC_DIR/openclaw.json"
TS="/Applications/Tailscale.app/Contents/MacOS/Tailscale"

# ---------------------------------------------------------------- prerequisites
say "Checking prerequisites"
command -v python3 >/dev/null || die "python3 not found (install Xcode Command Line Tools: xcode-select --install)"
OPENCLAW="$(command -v openclaw || true)"
if [ -z "$OPENCLAW" ]; then
  # nvm installs are not on PATH for non-login shells — look there too
  OPENCLAW="$(ls -d "$HOME"/.nvm/versions/node/*/bin/openclaw 2>/dev/null | tail -1 || true)"
fi
[ -n "$OPENCLAW" ] || die "openclaw not found. Install it first:  npm install -g openclaw   (then run: openclaw onboard)"
ok "openclaw: $OPENCLAW ($("$OPENCLAW" --version 2>/dev/null | head -1))"
[ -f "$OC_CFG" ] || die "$OC_CFG not found — run 'openclaw onboard' once, then re-run this script."
[ -x "$TS" ] || die "Tailscale.app not found. Install from https://tailscale.com/download/mac and sign in."
"$TS" status >/dev/null 2>&1 || die "Tailscale is installed but not connected — open Tailscale.app and sign in."
MAGIC="$("$TS" status --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))')"
ok "Tailscale MagicDNS name: $MAGIC"
CERTS="$("$TS" status --json | python3 -c 'import json,sys; print(",".join(json.load(sys.stdin).get("CertDomains") or []))')"
if [ -z "$CERTS" ]; then
  warn "HTTPS certificates are NOT enabled for your tailnet."
  warn "Open https://login.tailscale.com/admin/dns → 'HTTPS Certificates' → Enable HTTPS, then re-run."
  die "Tailscale HTTPS required for Tailscale Serve."
fi
ok "Tailnet HTTPS enabled ($CERTS)"

# ------------------------------------------------------------- openclaw config
say "Configuring OpenClaw ($OC_CFG)"
cp "$OC_CFG" "$OC_CFG.before-amisoria-$(date +%Y%m%d-%H%M%S)"
MAGIC="$MAGIC" python3 - "$OC_CFG" <<'PY'
import json, os, sys
p = sys.argv[1]; magic = os.environ["MAGIC"]
c = json.load(open(p))
gw = c.setdefault("gateway", {})
gw["bind"] = "loopback"
# OpenClaw >= 2026.9.1 verifies ownership of the Tailscale 443 route and refuses
# to start when it finds our hand-managed serve config -> keep its managed ingress OFF.
gw["tailscale"] = {"mode": "off"}
# Tailscale Serve proxies from loopback; >= 2026.9.1 returns 403 "proxy_attribution_required"
# unless the proxy is declared trusted.
gw["trustedProxies"] = ["127.0.0.1", "::1"]
cu = gw.setdefault("controlUi", {})
origins = set(cu.get("allowedOrigins") or [])
origins |= {"http://localhost:18789", "http://127.0.0.1:18789", f"https://{magic}"}
cu["allowedOrigins"] = sorted(origins)
cu.setdefault("allowInsecureAuth", True)
entries = c.setdefault("plugins", {}).setdefault("entries", {})
for name in ["openai", "anthropic", "google", "openrouter", "ollama", "microsoft"]:
    entries.setdefault(name, {})["enabled"] = True
d = c.setdefault("agents", {}).setdefault("defaults", {})
d.setdefault("compaction", {})["reserveTokensFloor"] = 6000
json.dump(c, open(p, "w"), indent=2, ensure_ascii=False)
print("  config updated")
PY
mkdir -p "$OC_DIR/settings"
python3 - "$OC_DIR/settings/tts.json" <<'PY'
import json, os, sys
p = sys.argv[1]
c = json.load(open(p)) if os.path.exists(p) else {}
t = c.setdefault("tts", {})
t["auto"] = "off"; t.setdefault("provider", "microsoft")
json.dump(c, open(p, "w"), indent=2)
print("  tts.auto = off (app drives voice itself)")
PY
TOKEN="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["gateway"]["auth"].get("token",""))' "$OC_CFG")"

# ---------------------------------------------------------------------- bridge
say "Installing the Amisoria bridge (launchd: com.amisoria.bridge)"
mkdir -p "$HOME/.amisoria"
cp "$HERE/amisoria-bridge.py" "$HOME/.amisoria/amisoria-bridge.py"
# bridge admin endpoints are gated by the gateway token
printf "%s" "$TOKEN" > "$HOME/.bridge-secret"; chmod 600 "$HOME/.bridge-secret"
[ -f "$HOME/.bridge-keys.json" ] || { echo '{}' > "$HOME/.bridge-keys.json"; chmod 600 "$HOME/.bridge-keys.json"; }
# the bridge shells out to openclaw — record where it lives
OC_BIN_DIR="$(dirname "$OPENCLAW")"
sed -i '' "s#^OPENCLAW_BIN = .*#OPENCLAW_BIN = \"$OPENCLAW\"#" "$HOME/.amisoria/amisoria-bridge.py" 2>/dev/null || true
PLIST="$HOME/Library/LaunchAgents/com.amisoria.bridge.plist"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.amisoria.bridge</string>
  <key>ProgramArguments</key>
  <array><string>/usr/bin/python3</string><string>$HOME/.amisoria/amisoria-bridge.py</string></array>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>$OC_BIN_DIR:/usr/bin:/bin:/usr/local/bin</string></dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/tmp/amisoria-bridge.log</string>
  <key>StandardErrorPath</key><string>/tmp/amisoria-bridge.log</string>
</dict>
</plist>
EOF
launchctl bootout "gui/$(id -u)/com.amisoria.bridge" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
sleep 2
if curl -s -m 5 -o /dev/null -w "%{http_code}" "http://127.0.0.1:18790/tts?path=/private/tmp/openclaw/x.mp3" | grep -q "404"; then
  ok "bridge is serving on 127.0.0.1:18790"
else
  warn "bridge did not answer yet — check /tmp/amisoria-bridge.log"
fi

# ------------------------------------------------------------- tailscale serve
say "Exposing gateway + bridge via Tailscale Serve (HTTPS, tailnet-only)"
"$TS" serve --bg --https=443 http://127.0.0.1:18789 >/dev/null 2>&1 &
sleep 6
"$TS" serve --bg --https=443 --set-path=/bridge http://127.0.0.1:18790 >/dev/null 2>&1 &
sleep 6
"$TS" serve status 2>/dev/null | sed 's/^/  /' || warn "could not read serve status"

# ---------------------------------------------------------------- persona rules
say "Adding Amisoria voice/avatar rules to the agent persona (AGENTS.md)"
WS="$HOME/.openclaw/workspace"; mkdir -p "$WS"
RULES="$HERE/workspace/AMISORIA-RULES.md"
if [ -f "$RULES" ]; then
  if grep -q "AMISORIA-RULES:BEGIN" "$WS/AGENTS.md" 2>/dev/null; then
    ok "persona rules already present — skipped"
  else
    [ -f "$WS/AGENTS.md" ] && cp "$WS/AGENTS.md" "$WS/AGENTS.md.before-amisoria-$(date +%Y%m%d-%H%M%S)"
    { echo; cat "$RULES"; } >> "$WS/AGENTS.md"
    ok "rules appended to $WS/AGENTS.md (see docs/*/persona-prompt.md)"
  fi
else
  warn "workspace/AMISORIA-RULES.md not found next to this script — skipped"
fi

# ---------------------------------------------------------------- restart gw
say "Restarting the OpenClaw gateway"
if launchctl print "gui/$(id -u)/ai.openclaw.gateway" >/dev/null 2>&1; then
  pkill -f "dist/index.js gateway" || true
  sleep 6
  pgrep -f "dist/index.js gateway" >/dev/null && ok "gateway restarted (launchd)" || warn "gateway not running — start it: openclaw gateway install"
else
  warn "gateway is not installed as a service. Run once:  openclaw gateway install"
fi

# -------------------------------------------------------------------- summary
if pmset -g 2>/dev/null | grep -qE "^ sleep +0"; then
  ok "system sleep is disabled (host stays reachable)"
else
  warn "This Mac will go to SLEEP when idle and the app will stop getting replies."
  warn "Run once:  sudo pmset -c sleep 0 disksleep 0   (see docs: Keep the host awake)"
fi
say "Done. Enter this in the Amisoria iPhone app → Settings:"
echo "    Host : $MAGIC"
echo "    Port : 443"
echo "    TLS  : ON"
echo "    Token: $TOKEN"
echo
echo "  After the first Connect, approve the phone once on this Mac:"
echo "    openclaw devices list            # shows the pending request id"
echo "    openclaw devices approve <id>"
echo
echo "  Optional — local/offline model:"
echo "    ollama pull qwen3:14b && echo ollama-local | openclaw models auth paste-api-key --provider ollama"
