#!/usr/bin/env python3
"""
amisoria-bridge — companion HTTP service that runs ON the OpenClaw host.

The gateway's tts.convert writes an mp3 and returns its PATH; it has no HTTP
file endpoint. This bridge, running on the same machine, serves that file:

    GET  /tts?path=~/.openclaw/media/tool-speech-synthesis/voice-YYY.mp3  ->  audio/mpeg

Admin endpoints (X-Auth header must equal the gateway token, kept in
~/.bridge-secret; without that file they answer 401, which is expected):

    POST /model-auth  {"provider":"anthropic","key":"sk-..."}  -> installs the
         provider API key via `openclaw models auth paste-api-key` and restarts
         the gateway so it reloads auth.
    GET  /balance  -> {"openrouter": <remaining USD>}

Configuration (environment variables; all optional):

    AMISORIA_BRIDGE_PORT         listen port            (default 18790)
    AMISORIA_BRIDGE_BIND         bind address           (default 127.0.0.1 —
                                 Tailscale Serve proxies from loopback, so
                                 nothing else needs to reach the bridge)
    AMISORIA_OPENCLAW_BIN        path to the openclaw CLI (default: the
                                 OPENCLAW_BIN line below, then `which openclaw`)
    AMISORIA_BRIDGE_PRUNE_HOURS  delete served TTS clips older than this many
                                 hours (default 24; 0 disables). OpenClaw never
                                 cleans ~/.openclaw/media/tool-speech-synthesis/
                                 itself (≈1 MB per hour of conversation).

Security: /tts only serves paths under /private/tmp/openclaw/ or
~/.openclaw/media/ (no ".."); admin endpoints are token-gated.

Install:
    macOS   — launchd, written by setup-host.sh (com.amisoria.bridge.plist)
    Linux   — systemd --user, see amisoria-bridge.service next to this file
"""
import os
import shutil
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import subprocess, urllib.parse, urllib.request, json, re

# OpenClaw < 2026.9 wrote TTS files under /private/tmp/openclaw/; 2026.9.1+ writes
# them under ~/.openclaw/media/tool-speech-synthesis/. Serve both, nothing else.
ALLOWED_PREFIXES = (
    "/private/tmp/openclaw/",
    os.path.expanduser("~/.openclaw/media/"),
)
TTS_DIR = os.path.expanduser("~/.openclaw/media/tool-speech-synthesis")
PORT = int(os.environ.get("AMISORIA_BRIDGE_PORT", "18790"))
BIND = os.environ.get("AMISORIA_BRIDGE_BIND", "127.0.0.1")
PRUNE_HOURS = float(os.environ.get("AMISORIA_BRIDGE_PRUNE_HOURS", "24"))
# Admin endpoints (/model-auth, /balance) require X-Auth == the gateway token
# (setup-host.sh copies it to ~/.bridge-secret). /tts stays open.
SECRET_FILE = os.path.expanduser("~/.bridge-secret")
KEYS_FILE = os.path.expanduser("~/.bridge-keys.json")   # provider -> key (balance queries)
PROVIDERS = {"openai", "anthropic", "google", "openrouter"}

# setup-host.sh rewrites the next line with the real path on macOS; on other
# hosts set AMISORIA_OPENCLAW_BIN or leave it to `which openclaw`.
OPENCLAW_BIN = os.path.expanduser("~/.nvm/versions/node/v24.18.0/bin/openclaw")
if os.environ.get("AMISORIA_OPENCLAW_BIN"):
    OPENCLAW_BIN = os.environ["AMISORIA_OPENCLAW_BIN"]
elif not os.path.exists(OPENCLAW_BIN):
    OPENCLAW_BIN = shutil.which("openclaw") or OPENCLAW_BIN
GATEWAY_PGREP = "dist/index.js gateway"


def restart_gateway(env):
    """Ask OpenClaw to restart its gateway so it reloads auth. Fall back to
    killing the process (launchd respawns it on macOS) only if the CLI refuses."""
    try:
        r = subprocess.run([OPENCLAW_BIN, "gateway", "restart"], capture_output=True, timeout=60, env=env)
        if r.returncode == 0:
            return "restart"
    except (OSError, subprocess.TimeoutExpired):
        pass
    subprocess.run(["pkill", "-f", GATEWAY_PGREP], capture_output=True, timeout=30)
    return "pkill"


def prune_loop():
    """Every hour, delete TTS clips older than PRUNE_HOURS. Only that folder."""
    while True:
        cutoff = time.time() - PRUNE_HOURS * 3600
        removed = 0
        try:
            for name in os.listdir(TTS_DIR):
                p = os.path.join(TTS_DIR, name)
                try:
                    if os.path.isfile(p) and os.path.getmtime(p) < cutoff:
                        os.remove(p)
                        removed += 1
                except OSError:
                    pass
        except OSError:
            pass
        if removed:
            print(f"[tts-bridge] pruned {removed} clip(s) older than {PRUNE_HOURS:g} h", flush=True)
        time.sleep(3600)


class Handler(BaseHTTPRequestHandler):
    def _authed(self):
        try:
            secret = open(SECRET_FILE).read().strip()
        except OSError:
            return False
        return secret and self.headers.get("X-Auth", "") == secret

    def _json(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        if url.path != "/model-auth":
            self.send_error(404)
            return
        if not self._authed():
            self._json(401, {"ok": False, "error": "unauthorized"})
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            provider = body["provider"]
            key = body["key"].strip()
        except Exception:
            self._json(400, {"ok": False, "error": "bad request"})
            return
        if provider not in PROVIDERS or not re.fullmatch(r"[A-Za-z0-9_\-\.]{8,300}", key):
            self._json(400, {"ok": False, "error": "invalid provider or key"})
            return
        env = dict(os.environ, PATH=os.path.dirname(OPENCLAW_BIN) + ":" + os.environ.get("PATH", ""))
        r = subprocess.run(
            [OPENCLAW_BIN, "models", "auth", "paste-api-key", "--provider", provider],
            input=(key + "\n").encode(), capture_output=True, timeout=60, env=env)
        if r.returncode != 0:
            self._json(502, {"ok": False, "error": r.stderr.decode()[:150]})
            return
        how = restart_gateway(env)
        try:
            keys = json.load(open(KEYS_FILE)) if os.path.exists(KEYS_FILE) else {}
            keys[provider] = key
            json.dump(keys, open(KEYS_FILE, "w"))
            os.chmod(KEYS_FILE, 0o600)
        except OSError:
            pass
        self._json(200, {"ok": True, "restart": how})

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == "/balance":
            if not self._authed():
                self._json(401, {"ok": False, "error": "unauthorized"})
                return
            try:
                keys = json.load(open(KEYS_FILE))
                req = urllib.request.Request("https://openrouter.ai/api/v1/credits",
                    headers={"Authorization": "Bearer " + keys["openrouter"]})
                d = json.load(urllib.request.urlopen(req, timeout=15))["data"]
                remaining = float(d.get("total_credits", 0)) - float(d.get("total_usage", 0))
                self._json(200, {"ok": True, "openrouter": round(remaining, 2)})
            except Exception as e:
                self._json(502, {"ok": False, "error": str(e)[:120]})
            return
        if url.path != "/tts":
            self.send_error(404)
            return
        path = os.path.expanduser((urllib.parse.parse_qs(url.query).get("path") or [""])[0])
        if not path.startswith(ALLOWED_PREFIXES) or ".." in path:
            self.send_error(403)
            return
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError:
            self.send_error(404)
            return
        if not data:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "audio/mpeg")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print("[tts-bridge]", fmt % args, flush=True)


if __name__ == "__main__":
    if PRUNE_HOURS > 0:
        threading.Thread(target=prune_loop, daemon=True).start()
    print(f"[tts-bridge] listening on {BIND}:{PORT} (openclaw: {OPENCLAW_BIN}, prune: {PRUNE_HOURS:g} h)", flush=True)
    ThreadingHTTPServer((BIND, PORT), Handler).serve_forever()
