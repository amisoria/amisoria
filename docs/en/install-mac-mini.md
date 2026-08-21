# Nuvaryn Setup Guide — Mac mini host + iPhone

This guide uses an **always-on Mac mini (Apple Silicon)** as Iris's brain (the OpenClaw gateway) and an
**iPhone** as her face and voice. Budget about 30 minutes. No public IP, no port-forwarding, no web server:
the iPhone reaches your Mac mini over a private, encrypted **Tailscale** network.

> In one line: `iPhone (Nuvaryn app) ──Tailscale HTTPS──▶ Mac mini (OpenClaw + Nuvaryn bridge) ──▶ AI providers`
>
> Your conversations travel only between your phone and your Mac mini. Nuvaryn runs no servers of its own.

---

## 0. Checklist

| Item | Notes |
|---|---|
| Mac mini | macOS 14+, Apple Silicon (M1+); 16 GB RAM+ recommended if you want a local model |
| iPhone | iOS 17+ |
| Tailscale account | Free plan is enough (https://tailscale.com) |
| At least one AI provider API key | OpenAI / Anthropic / Google AI Studio / OpenRouter — you can add more later inside the app |
| Time | ~30 minutes |

---

## 1. Install OpenClaw on the Mac mini

1. Install Node.js (nvm recommended):
   ```bash
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash
   source ~/.zshrc
   nvm install --lts
   ```
2. Install OpenClaw and run its onboarding (picks a model, creates the gateway token):
   ```bash
   npm install -g openclaw
   openclaw onboard
   ```
3. Install the gateway as a login service so it survives reboots:
   ```bash
   openclaw gateway install
   ```
4. Sanity check:
   ```bash
   openclaw models status
   ```

> **Where do API keys go?** `openclaw models auth paste-api-key --provider openai` (or anthropic / google / openrouter).
> You can also change them later from the iPhone app (Settings → Keys) — no terminal needed.

---

## 2. Install Tailscale and enable HTTPS

1. Install **Tailscale.app** on the Mac mini (https://tailscale.com/download/mac) and sign in.
2. Install the **Tailscale** app on the iPhone (App Store), sign in with the **same account**, switch it on.
3. In the Tailscale admin console, open **https://login.tailscale.com/admin/dns** → **HTTPS Certificates** → **Enable HTTPS** (one-time, free).
   This lets the Mac mini serve `https://<machine>.<tailnet>.ts.net`.

---

## 3. Run the Nuvaryn host setup script

One script applies every setting we learned the hard way (safe to re-run):

```bash
git clone https://github.com/GlenNuvaryn/nuvaryn.git
cd nuvaryn/host
bash setup-host.sh
```

It will:
- bind OpenClaw to loopback and publish it through Tailscale Serve; add your MagicDNS name to the allowed origins (without this you get `origin not allowed`);
- enable the openai / anthropic / google / openrouter / ollama / microsoft plugins;
- install the **Nuvaryn bridge** (voice audio, key updates, balance) as a launchd service;
- configure Tailscale Serve for gateway + bridge over HTTPS;
- **print the Host / Port / Token to type into the iPhone.**

---

## 4. Set up the Nuvaryn app on the iPhone

1. Install **Nuvaryn** from the App Store and go through the first-run guide (try **Demo mode** first if you like).
2. Tap ⚙️ → **Gateway**:
   - Host: the MagicDNS name the script printed (e.g. `mac-mini.tail1234.ts.net`)
   - Port: `443`
   - Use TLS: **on**
   - Keys → Gateway Token: the token the script printed
3. Back in chat, tap **Connect**. The first time you'll see a 🔐 pairing message with a request ID.
4. On the Mac mini, approve this phone (**once**):
   ```bash
   openclaw devices list              # shows the pending request id
   openclaw devices approve <request-id>
   ```
   > The pending list is cleared whenever the gateway restarts — approve promptly.
5. Tap **Connect** again → green "Connected". Say hi to Iris.

---

## 5. Optional: local offline model (Ollama)

On the Mac mini:

```bash
curl -fsSL https://ollama.com/install.sh | sh        # or download the app from ollama.com
ollama pull qwen3:14b                                 # ~9 GB; the sweet spot for an 18 GB machine
echo ollama-local | openclaw models auth paste-api-key --provider ollama
```

Then add the model to OpenClaw's roster (`~/.openclaw/openclaw.json` → `agents.defaults.models` → `"ollama/qwen3:14b": {"alias": "Local Qwen"}`) and restart the gateway.
"Local Qwen" appears in the app's model picker.

> **Honest limitation:** current OpenClaw does **not** inject the persona (system prompt) for Ollama models, so a local model
> won't call itself Iris and can't use tools (e.g. weather). Known upstream issue
> ([#74579](https://github.com/openclaw/openclaw/issues/74579)). Treat local models as an offline fallback; use cloud models day to day.

---

## 6. Verify & troubleshoot

| Symptom | Cause / fix |
|---|---|
| `origin not allowed` | `gateway.controlUi.allowedOrigins` lacks `https://<MagicDNS>`. Re-run `setup-host.sh` or add it and restart the gateway. |
| `control ui requires device identity` | Old app build or a non-TLS connection. Use port 443 with TLS on. |
| `pairing required` keeps appearing | Not approved yet, or the gateway restarted before approval. `openclaw devices list` → approve the new id. |
| Connected but **no voice**, every reply female | Server voice unreachable → app fell back to iPhone's built-in voice. Check the bridge: `curl -s -o /dev/null -w "%{http_code}" https://<MagicDNS>/bridge/tts?path=x` should print `404` (alive); `000` means it's down → `launchctl kickstart -k gui/$(id -u)/com.nuvaryn.bridge`. |
| Model returns `402` / `429` | 402 = OpenRouter has no credits; 429 = free quota exhausted or the key lacks that model (Google's free tier has Flash only, no Pro). |
| Local model: `Auto-compaction could not recover` | `agents.defaults.compaction.reserveTokensFloor` too large (fatal for 33k-context models). The script sets 6000. You can also tap ✏️ New conversation in the app. |
| Replies show "Audio reply" | Server-side auto-TTS is on. The script sets `tts.auto` to off. |
| App can't connect after a Mac mini reboot | Gateway and bridge are launchd services and come back on their own; Tailscale Serve config persists. If not, re-run `setup-host.sh`. |

Done — next, read the [User Guide](user-guide.md).
