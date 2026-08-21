# Nuvaryn Privacy Policy / 隱私權政策

_Last updated / 最後更新: 2026-08-21_

[English](#english) · [繁體中文](#繁體中文)

---

## English

Nuvaryn ("the App") is an iOS client for a **self-hosted** OpenClaw gateway. This policy explains what the App does — and, more importantly, what it does not do — with your data.

### What we do NOT do
- Nuvaryn operates **no servers of its own**. There is no Nuvaryn account, no sign-in, no analytics SDK, no advertising SDK, and no crash-reporting service that receives your data.
- We do **not** collect, store, transmit, or sell your conversations, voice recordings, API keys, contacts, location, or identifiers.
- We do **not** track you across apps or websites.

### Where your data goes
The App talks exclusively to endpoints **you configure**:
1. **Your own OpenClaw gateway** (typically a Mac at your home), over an encrypted connection (TLS / your private Tailscale network). Your messages, the assistant's replies, and per-sentence speech audio travel only between your iPhone and that machine.
2. **AI providers you choose** (e.g. OpenAI, Anthropic, Google, OpenRouter) are contacted **by your gateway**, not by the App, using API keys **you** supplied. Their handling of that traffic is governed by their own privacy policies.
3. Speech synthesis for server voice is performed by your gateway's configured engine (e.g. Microsoft neural voices); the audio file is fetched from your gateway.

### Data stored on your iPhone
- **Keychain (encrypted):** your gateway token, any provider API keys you enter, and the device's Ed25519 identity key used to authenticate to your gateway.
- **App preferences (UserDefaults):** host name, port, TLS flag, chosen character, language and model preferences, and whether you completed the first-run guide.
- Conversation history is **not** persisted by the App; it is kept by your gateway and re-fetched on connect.
You can erase everything by deleting the App (the Keychain items are removed when you delete the app and its data).

### Microphone & speech recognition
With your permission, the App uses the microphone and Apple's on-device / Apple-operated speech recognition to turn your voice into text. Audio is used only for that purpose and is processed by iOS under Apple's privacy policy. Nothing is recorded or stored by the App.

### Demo mode
Demo mode runs entirely on the device with scripted replies and Apple's on-device voices. No network connection is made.

### Children
The App is not directed at children under 13 and does not knowingly collect any data from anyone.

### Changes
We will post any changes to this page. Material changes will also be noted in the App's release notes.

### Contact
Questions: **[contact email — to be published]**
Repository: https://github.com/GlenNuvaryn/nuvaryn

---

## 繁體中文

Nuvaryn(以下稱「本 App」)是一個連接**自架 OpenClaw gateway** 的 iOS 用戶端。本政策說明本 App 對你的資料做了什麼——更重要的是,沒有做什麼。

### 我們「不」做的事
- Nuvaryn **沒有自己的伺服器**。沒有帳號、不需登入、沒有分析 SDK、沒有廣告 SDK、沒有任何會接收你資料的錯誤回報服務。
- 我們**不會**蒐集、儲存、傳送或販售你的對話、語音、API 金鑰、聯絡人、位置或任何識別碼。
- 我們**不會**跨 App 或網站追蹤你。

### 你的資料去了哪裡
本 App 只會連到**你自己設定**的端點:
1. **你自己的 OpenClaw gateway**(通常是你家裡的一台 Mac),透過加密連線(TLS / 你的私人 Tailscale 網路)。你的訊息、助理的回覆、逐句語音音檔,只在你的 iPhone 與那台機器之間流動。
2. **你選擇的 AI 供應商**(如 OpenAI、Anthropic、Google、OpenRouter)是由**你的 gateway** 去連,不是本 App;使用的是**你自己**提供的 API 金鑰。相關資料處理受各供應商自己的隱私權政策規範。
3. 伺服器語音由你的 gateway 所設定的引擎(如 Microsoft 神經語音)合成,音檔自你的 gateway 取得。

### 存放在你 iPhone 上的資料
- **Keychain(加密)**:Gateway token、你輸入的供應商 API 金鑰、以及用來向你的 gateway 驗證身分的裝置 Ed25519 金鑰。
- **App 偏好設定(UserDefaults)**:主機名稱、連接埠、TLS 開關、所選角色、語言與模型偏好、是否完成首次導引。
- 對話歷史**不**由本 App 保存,而是存在你的 gateway,連線時重新取得。
刪除 App(連同資料)即可清除以上全部內容。

### 麥克風與語音辨識
在你授權下,本 App 使用麥克風與 Apple 的語音辨識(裝置端 / Apple 營運)將你的語音轉成文字。音訊僅用於此目的,由 iOS 依 Apple 隱私權政策處理;本 App 不錄製、不儲存任何音訊。

### 示範模式
示範模式完全在裝置上執行,使用預先準備的台詞與 Apple 裝置內建語音,不會建立任何網路連線。

### 兒童
本 App 並非針對 13 歲以下兒童設計,亦不會蓄意蒐集任何人的資料。

### 變更
本政策如有修改將公布於本頁;重大變更亦會於 App 更新說明中註明。

### 聯絡
問題請洽:**[聯絡信箱 — 待公布]**
原始碼與文件:https://github.com/GlenNuvaryn/nuvaryn
