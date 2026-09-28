# OpenClaw compatibility

OpenClaw ships several releases a month. Amisoria does **not** chase every one of them. Instead:

- **The app depends on a small, stable surface** of the gateway (listed below), not on a version number. A release that leaves that surface alone keeps working.
- **We run one version end-to-end at a time** — voice, lip-sync, model switching, API-key writes, device pairing — and mark it *verified*. New releases wait about a week after they ship (so the community finds the regressions first), then get tested.
- **The app tells you where you stand.** From Amisoria 1.3, Settings → 連線網址 shows the connected gateway's version with a dot: green = verified, orange = untested but everything the app needs is present, red = something the app calls is missing (with the reason). Older app versions simply try to connect.

## What Amisoria actually uses

| Surface | Detail |
|---|---|
| WebSocket protocol | `4` (checked in the `connect` handshake) |
| Connect params | control-ui style client, `client.buildId` present (required since 2026.9.1), Ed25519 device identity v2, gateway token |
| RPC methods | `chat.startup`, `chat.send`, `sessions.messages.subscribe`, `sessions.patch`, `models.list`, `tts.status`, `tts.providers`, `tts.setProvider`, `tts.convert`, `config.get`, `config.patch`, `health` |
| Streamed events | `session.message` (assistant deltas may be rewritten mid-run; the app handles that) |
| Files (via the bridge) | TTS output under `~/.openclaw/media/` (2026.9.1+) or `/private/tmp/openclaw/` (older) |
| Host | `openclaw devices approve` for pairing; `gateway.tailscale.mode: "off"` and `gateway.trustedProxies` when behind Tailscale Serve |

If a future release renames or removes one of those methods, the app shows a red dot naming the missing method, and this page will say what to do.

## Status by OpenClaw version

| OpenClaw | Status | Amisoria | Notes |
|---|---|---|---|
| **2026.9.6** | **Verified** | 1.3 | Full flow passed on a fresh Mac mini (Node 26, 2026-09-27): text, server voice + lip-sync, mic, character switch, model switch, API-key write, 10-turn conversation. Retires `sessions.compaction.*` (unused by us); invalid config now points to `openclaw doctor --fix`. On a brand-new install the very first reply can take noticeably longer (the agent runs its bootstrap ritual and the Gateway may still be downloading the model catalog) — wait it out once. **Retires `agents.defaults.compaction.reserveTokensFloor`** and rejects it if present (config invalid → CLI refuses, API-key apply fails, Gateway won't restart); `setup-host.sh` from 2026-09-28 on prunes it automatically, older copies wrote it — run `openclaw doctor --fix` or re-run the script. OpenAI models now run through the codex plugin and the reply stream re-sends the completed text with `replace:true`; Amisoria 1.3 handles that, 1.2 shows and speaks such replies twice. |
| 2026.9.5 | Not tested | — | Changelog reviewed; no changes to the surface above. Upgrade notes: 9.5 defers legacy pairing/session repairs to `openclaw doctor --fix` — run it once after upgrading if the Gateway reports pending repairs. |
| 2026.9.4 | Not tested | — | Changelog reviewed; nothing touching the surface above. |
| 2026.9.3 | Not tested | — | **Breaking for hosts:** requires Node 24.16+ (24.x) or Node 26.1+ (26 recommended). Upgrade Node *before* OpenClaw or SQLite text truncation can corrupt history. |
| 2026.9.2 | Not tested | — | Adds WebSocket payload compression for large chat startups; we want to test this explicitly before marking it verified. |
| 2026.9.1 | Verified | 1.1+ | The version our host script and guides were first written against. Upgrade pitfalls from 2026.7 are documented in the [install guide](install-mac-mini.md#upgrading-openclaw--things-to-check). |
| 2026.7.x | Worked with 1.0 | 1.0 | Amisoria 1.0 was developed against it. Not re-tested since 1.1 started sending `client.buildId`. |

"Not tested" means exactly that — not "broken". If you run one of those versions and it works (or doesn't), a note in [Issues](https://github.com/amisoria/amisoria/issues) helps everyone.

## Upgrading

1. Read the version's row above and the [upgrade checklist](install-mac-mini.md#upgrading-openclaw--things-to-check).
2. Back up `~/.openclaw/openclaw.json`. Releases retire keys (2026.9.6: `agents.defaults.compaction.reserveTokensFloor`, `gateway.controlUi.allowInsecureAuth`); a retired key left in the file makes the config invalid and the Gateway refuses to start. `openclaw config validate` tells you; do not re-add keys by hand.
3. Upgrade Node first if the release requires it, then `npm i -g openclaw@<version>`.
4. Run the Gateway in the foreground once (`openclaw gateway`) and read the first screen of output — the launchd service sends stderr to `/dev/null`, so a config error otherwise looks like a silent restart loop.
5. Re-run `host/setup-host.sh`; it re-applies the settings the app depends on and updates the bridge.
6. Open Amisoria → Settings and check the Gateway version dot.

## Policy in one paragraph

Verified versions are the ones listed as such above; everything else is best-effort. We pin our own host to the newest verified version, test new releases about a week after they appear, and move the *verified* mark forward when the full flow passes. We do not backport fixes to old OpenClaw versions, and we will say so here if a release ever breaks the surface the app needs.
