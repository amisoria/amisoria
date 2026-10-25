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

Great for talking while doing something else. With **Barge-in** (Settings → Voice, available since 1.4) you can also cut her off mid-sentence: just start talking while she speaks.

**Bluetooth headsets and car audio** (1.5): while hands-free is on, a headset with a microphone is used for both listening and speaking, in call quality (iOS switches it to the HFP profile); without hands-free, playback uses the high-quality A2DP route. The chat shows a 🎧 line whenever the audio route changes. Take the earbuds out mid-reply and she stops; the rest of the reply appears as text instead of coming out of the speaker. (Up to 1.4.4, a headset only worked without barge-in — with barge-in on, her voice went to the phone's speaker.)

---

## Voice engine

Settings → Voice → **Voice engine** (Amisoria 1.5 and later; 1.4.x offers Microsoft and ElevenLabs only):

| Choice | What it means |
|---|---|
| **Microsoft (free)** | Neural voices synthesized on your gateway, no key needed. The default; the four characters each have their own voice in 20 languages. |
| **Gateway default** | Whatever TTS provider your gateway has active. This is how you use a **local voice** such as Piper or Kokoro: point OpenClaw's `openai` TTS provider at your local server, make it the gateway's provider, and pick this. The voice and model follow the host's settings; lip-sync works from the returned audio. |
| Google / OpenAI / OpenRouter / xAI / … | Every provider your gateway reports (`tts.providers`), marked "not set up" until the host has its key. The voice is the one configured on the host. |

The choice is sent with every request; the app never changes the host's own preference. If synthesis fails, the reply is read by the iPhone's built-in voice and the chat shows the gateway's reason plus a hint when it is a known one (Microsoft endpoint moved, Microsoft plugin disabled, provider has no key). The built-in voice has no male Chinese option on iOS, so Lucas sounds female in Chinese until the server voice is back, and the character's lips don't move for built-in speech.

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

**Speed tip:** if your model has a "thinking" / reasoning mode, turn it off for voice conversations (in OpenClaw's model settings on the host). A user measured a large drop in time-to-first-word with thinking off; for chat the extra reasoning rarely changes the answer. Keep it on for tasks where it matters.

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
5. **Barge-in**: with "Barge-in (experimental)" enabled in Settings you can interrupt Iris while she is speaking. The trade-off is call-mode voice processing, which makes her voice sound a little duller; with it off, Iris listens again only after she has finished.
6. **Very long conversations get slow, confused and expensive**: every message sends the whole history of the conversation to the model. Once a conversation has grown to a few hundred messages (measured: 344 messages, ~100k tokens per turn), a small model starts answering the wrong question after a web search, replies take 20–38 s, and a single "hi" after a break costs ~100k input tokens. The fix is simple: tap ✏️ (top right) for a new conversation and replies are back to a few seconds. Start a new one whenever you change topic or it feels slow.

---

## Privacy

- Conversations flow only between your iPhone, your Mac mini, and the AI providers you chose.
- Amisoria operates **no** servers that collect your conversations, keys, or usage.
- See the [Privacy Policy](../../PRIVACY.md).
