# Amisoria User Guide

Amisoria is an **AI companion with a voice, a face, and your language**.
The default character is **Iris**; her brain runs on your own Mac mini (see the [Setup Guide](install-mac-mini.md)),
the phone is her face and voice.

---

## First launch

A four-page guide explains what she does and how she connects. The last page offers two paths:

- **Try demo mode** — no server needed. Iris talks to you with scripted lines; voice, expressions and lip-sync are real. A good first taste.
- **I already have a gateway** — go straight to settings.

Demo mode is always reachable from **Settings → Try demo mode**; "Leave demo" in the status bar (or tapping Connect) exits it.

---

## Main screen (chat)

| Where | What |
|---|---|
| Top-left 🔊 | Voice on/off (text only when off) |
| Top-left 👤 | Open the **Stage** (full-screen 3D character) |
| Top-right ✏️ | **New conversation** (archives history; recommended when switching topics or using a local model) |
| Top-right ⚙️ | Settings |
| Status bar | Green dot = connected, latency in ms; Connect / Disconnect on the right |
| Bottom 🎙️ | Voice input: tap to listen, tap again to send |
| Bottom field | Type; swipe the list or tap blank space to dismiss the keyboard |

---

## Stage (face to face)

- On first entry **tap the screen once** to wake audio (iOS requires a touch to start sound).
- The capsule at the top shows the current character; tap it to switch between **Iris / Iris (US) / Lucas / Lucas (US)** — voices follow. The choice is remembered.
- Subtitles appear word by word as she speaks; her expressions and gestures are cues she writes into her own replies (you see the expression, never the markup).
- If the app sat in the background for a while, iOS may reclaim the stage; it reloads automatically — **tap once more** to restore sound.

---

## Natural conversation (hands-free)

Settings → Voice → **Natural conversation (hands-free)**. The mic button becomes a hands-free switch:

1. Tap once → hands-free on (mic stays orange).
2. Finish speaking and **pause ~1.5 s** — it sends automatically.
3. The mic pauses while Iris answers (she never hears herself), then reopens.
4. Tap the mic again → off.

Great for talking while doing something else. Turn-taking only for now; interrupting her mid-sentence is planned.

---

## 20 languages

Iris **answers in the language you use** — voice and lip-sync switch with it, nothing to configure:
English, Traditional Chinese, Simplified Chinese, Japanese, Korean, Spanish, Hindi, French, German, Portuguese, Arabic, Indonesian, Italian, Vietnamese, Turkish, Thai, Russian, Dutch, Polish, Filipino, Bengali.

Settings → Language fine-tunes:

- **Speech input language**: what you speak into the mic ("Auto" follows the system).
- **Preferred language**: the voice used when a reply is in Latin script. Set it for languages auto-detection can't tell apart (e.g. Filipino).
- **Arabic dialect**: Standard (MSA) / Egyptian / Gulf / Levantine / Moroccan — text alone can't reveal a dialect, so choose yours.

---

## Models

Settings → Model, grouped by **OpenAI / Anthropic / Gemini / OpenRouter / Local**; takes effect from the next reply and is stored server-side.
Your OpenRouter balance shows here (other providers expose no balance API).

| You want | Suggestion |
|---|---|
| Everyday, cheap | GPT (gpt-5.4-mini), Claude Haiku, Gemini Flash |
| Quality first | Claude Sonnet |
| Ultra-cheap | DeepSeek (via OpenRouter) |
| Offline / privacy | Local Qwen (see limits below) |

---

## Keys

Settings → Keys:
- **Gateway Token**: this phone's pass to your Mac mini.
- **OpenAI / Anthropic / Gemini / OpenRouter**: your Mac mini's keys to each provider. Paste, tap Apply — written securely to the Mac mini, which restarts its service (reconnects in ~10 s).
Keys live only in the iPhone Keychain and on your Mac mini. Nothing is uploaded anywhere.

---

## Known limitations (please read)

1. **Male voice in demo / offline**: demo mode and server-voice fallback use the iPhone's built-in voices. iPhones **usually ship without a male Chinese voice**, so Lucas may sound female there.
   Fix: **Settings → Accessibility → Spoken Content → Voices → Chinese** and download a male voice; the app picks it up automatically. English male voices are normally preinstalled.
   Connected mode is unaffected (the cloud male voice is always available).
2. **Local models have no persona and no tools**: OpenClaw currently doesn't inject the system prompt for Ollama models (upstream issue), so Local Qwen won't call itself Iris or check the weather. Treat it as an offline fallback.
3. **Stage wake-up**: after any stage reload you must tap once for sound (iOS audio policy).
4. **Speech recognition**: iOS restarts recognition roughly every 60 s; hands-free handles it automatically — split very long monologues.
5. **Barge-in**: your voice isn't captured while Iris is speaking; planned.

---

## Privacy

- Conversations flow only between your iPhone, your Mac mini, and the AI providers you chose.
- Amisoria operates **no** servers that collect your conversations, keys, or usage.
- See the [Privacy Policy](../../PRIVACY.md).
