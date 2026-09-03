# Persona & Prompt Guide (pitfalls we hit)

Amisoria **speaks** OpenClaw's replies aloud and drives a 3D character's lips and
face with them. Quirks that are harmless in a text chat become "reading a URL
out loud" or "thinking out loud in English before answering". This page lists
the pitfalls we actually hit and the **prompt-level fixes** — all of them live in
`~/.openclaw/workspace/AGENTS.md` (OpenClaw's persona file); no code changes.

> Shortcut: `host/setup-host.sh` appends
> [`host/workspace/AMISORIA-RULES.md`](../../host/workspace/AMISORIA-RULES.md)
> to your `AGENTS.md` (marker-guarded, safe to re-run). Or paste that file's
> contents at the end of `AGENTS.md` by hand.

## Pitfall 1: the model writes its inner monologue into the answer (Gemini especially)

**Symptom**: the reply opens with an English third-person narration — "Glen is
back. He's asking where I'm going. I'll respond warmly." — followed by the real
answer. The voice reads the whole preamble aloud.

**Cause**: thinking models such as `gemini-3-flash-preview` occasionally put
their planning into the body text. OpenClaw already routes proper thinking
blocks separately, but here the text *is* the body, so nothing downstream can
filter it structurally.

**Fix** (AGENTS.md):
```
- Output ONLY the words meant for the user. Never include internal reasoning,
  planning, or third-person narration ("The user is back… I will respond warmly.")
  — not a single sentence of it.
- Start every reply in the user's current language; never open with a
  self-narration in another language.
```
This works in practice; if it still leaks occasionally, move off the preview model.

## Pitfall 2: markdown read aloud

**Symptom**: the voice says "star star", "hash", or subtitles show `**bold**` and table pipes.

**Fix**: the app strips markdown, but the cleanest fix is at the source:
```
Do not use markdown formatting (no **bold**, no tables; lists are fine as plain lines)
— replies are displayed as plain text and spoken aloud.
```

## Pitfall 3: URLs and citation tokens

**Symptom**: "h t t p s colon slash slash order dot nidin dot shop…"; or subtitles
showing `⍰cite🚢turn7search2` (OpenAI web-search citation markers wrapped in
private-use Unicode, which iOS renders as boxes and ships).

**Fix**: the app already drops URLs from speech and strips citation tokens
entirely; add this so sources look tidy too:
```
Do not paste raw URLs into sentences that will be read aloud. If you must cite a
source, put the site name in parentheses at the end of the sentence, e.g. "(example.com)".
```

## Pitfall 4: mixed languages

**Symptom**: one sentence mixes two languages; per-sentence language detection
switches voices mid-sentence and it sounds broken.

**Fix**:
```
Always reply in the language of the user's latest message. Do not mix languages
in one sentence unless the user does. If the user's language is ambiguous
(a bare emoji or a name), keep the language of the previous turn.
```

## Pitfall 5: emoji

**Symptom**: the voice says "smiling face", or the character wears one
expression all the time.

**Fix**: Amisoria lifts emoji out of the reply and plays them as **facial
expressions** (never spoken or shown). Tell the model so, give it the map
(🙂😊 warm · 🤔 thinking · 😌 calm · 😅 oops · 😮 surprise · 🥺 concern ·
😉 playful · 😐 neutral) and ask for at most one per reply, at the start or end
of a sentence.

## Pitfall 6: "As an AI, I don't have feelings"

**Symptom**: asked where she's going this afternoon, she answers "As an AI, I
don't go anywhere."

**Fix**: declare the identity at the top of AGENTS.md: `YOU ARE IRIS — a warm,
elegant, empathetic AI companion. Never say you are "an assistant without feelings".`

---

Editing `AGENTS.md` needs **no gateway restart** — the next message picks it
up. Back it up first (`cp AGENTS.md AGENTS.md.bak`).
