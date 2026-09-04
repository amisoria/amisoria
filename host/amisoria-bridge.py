#!/usr/bin/env python3
"""
amisoria-bridge — companion HTTP service that runs ON the OpenClaw host (Mac mini).

The gateway's tts.convert writes an mp3 and returns its PATH; it has no HTTP
file endpoint. This bridge, running on the same machine, serves that file:

    GET  /tts?path=/private/tmp/openclaw/tts-XXXX/voice-YYY.mp3  ->  audio/mpeg

Admin endpoints (X-Auth header must equal the gateway token, kept in
~/.bridge-secret):

    POST /model-auth  {"provider":"anthropic","key":"sk-..."}  -> installs the
         provider API key via `openclaw models auth paste-api-key` and restarts
         the gateway (launchd respawns it).
    GET  /balance  -> {"openrouter": <remaining USD>}

Security: /tts only serves paths under /private/tmp/openclaw/ or ~/.openclaw/media/ (no ".."); admin
endpoints are token-gated. Bind to the Tailscale interface or firewall port
18790 to your tailnet.

Install (launchd, see docs/install-mac-mini.md):
    ~/.amisoria/amisoria-bridge.py + com.amisoria.bridge.plist
"""
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import subprocess, urllib.parse, urllib.request, json, os, re

# LOCAL edition: runs ON the gateway host (Mac mini). No SSH hop.
# OpenClaw < 2026.9 wrote TTS files under /private/tmp/openclaw/; 2026.9.1+ writes
# them under ~/.openclaw/media/tool-speech-synthesis/. Serve both, nothing else.
ALLOWED_PREFIXES = (
    "/private/tmp/openclaw/",
    os.path.expanduser("~/.openclaw/media/"),
)
PORT = 18790
# Admin endpoints (/model-auth, /balance) require X-Auth == the gateway token
# (a copy lives in ~/.bridge-secret on Mac A). /tts stays open as before.
SECRET_FILE = os.path.expanduser("~/.bridge-secret")
KEYS_FILE = os.path.expanduser("~/.bridge-keys.json")   # provider -> key (balance queries)
PROVIDERS = {"openai", "anthropic", "google", "openrouter"}

OPENCLAW_BIN = os.path.expanduser("~/.nvm/versions/node/v24.18.0/bin/openclaw")
GATEWAY_PGREP = "dist/index.js gateway"

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
        # gateway must reload auth → kill it; launchd respawns in seconds
        subprocess.run(["pkill", "-f", GATEWAY_PGREP], capture_output=True, timeout=30)
        try:
            keys = json.load(open(KEYS_FILE)) if os.path.exists(KEYS_FILE) else {}
            keys[provider] = key
            json.dump(keys, open(KEYS_FILE, "w"))
            os.chmod(KEYS_FILE, 0o600)
        except OSError:
            pass
        self._json(200, {"ok": True})

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
        path = (urllib.parse.parse_qs(url.query).get("path") or [""])[0]
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
    print(f"[tts-bridge] listening on 0.0.0.0:{PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
