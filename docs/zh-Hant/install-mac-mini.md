# Nuvaryn 安裝手冊 — Mac mini 主機 + iPhone

本手冊以 **一台全天候開機的 Mac mini(Apple Silicon)** 作為 Iris 的大腦(OpenClaw gateway),
**iPhone** 作為互動介面。整套流程約 30 分鐘。不需要公網 IP、不需要開防火牆埠、不需要架網站:
iPhone 透過 **Tailscale** 私人加密網路找到你的 Mac mini。

> 架構一句話:`iPhone (Nuvaryn app) ──Tailscale HTTPS──▶ Mac mini (OpenClaw + Nuvaryn bridge) ──▶ 各家 AI 模型`
>
> 你的對話只在你的手機與你的 Mac mini 之間流動,不經過 Nuvaryn 的任何伺服器。

---

## 0. 準備清單

| 項目 | 說明 |
|---|---|
| Mac mini | macOS 14 以上,Apple Silicon(M1 以上;本地模型建議 16 GB RAM 以上) |
| iPhone | iOS 17 以上 |
| Tailscale 帳號 | 免費方案即可(https://tailscale.com) |
| 至少一家 AI 供應商的 API key | OpenAI / Anthropic / Google AI Studio / OpenRouter 任一;可之後在 app 內新增 |
| 時間 | 約 30 分鐘 |

---

## 1. 在 Mac mini 安裝 OpenClaw

1. 安裝 Node.js(建議用 nvm):
   ```bash
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash
   source ~/.zshrc
   nvm install --lts
   ```
2. 安裝 OpenClaw 並完成初始設定(會問你要用哪家模型、並產生 gateway token):
   ```bash
   npm install -g openclaw
   openclaw onboard
   ```
3. 把 gateway 裝成開機自動啟動的常駐服務:
   ```bash
   openclaw gateway install
   ```
4. 確認它在跑:
   ```bash
   openclaw models status
   ```

> **金鑰放哪裡?** 用 `openclaw models auth paste-api-key --provider openai`(或 anthropic / google / openrouter)
> 逐一貼上。之後也可以直接在 iPhone app 的「設定 → 金鑰」更換,不必再碰終端機。

---

## 2. 安裝 Tailscale 並開啟 HTTPS

1. 在 Mac mini 安裝 **Tailscale.app**(https://tailscale.com/download/mac),用你的帳號登入。
2. 在 iPhone 安裝 **Tailscale** app(App Store),用**同一個帳號**登入並開啟連線。
3. 到 Tailscale 管理後台 **https://login.tailscale.com/admin/dns** → 找到 **HTTPS Certificates** → 按 **Enable HTTPS**(一次性,免費)。
   這一步讓 Mac mini 能提供 `https://<你的機器名>.<tailnet>.ts.net` 的加密連線。

---

## 3. 執行 Nuvaryn 主機設定腳本

這個腳本把所有「踩過坑」的設定一次做完(可重複執行):

```bash
git clone https://github.com/GlenNuvaryn/nuvaryn.git
cd nuvaryn/host
bash setup-host.sh
```

它會:
- 把 OpenClaw 設為只聽本機、透過 Tailscale Serve 對外;把你的 MagicDNS 名稱加進允許的來源(沒做這步會出現 `origin not allowed`);
- 啟用 openai / anthropic / google / openrouter / ollama / microsoft 外掛;
- 安裝 **Nuvaryn bridge**(提供語音音檔、金鑰更換、餘額查詢)為常駐服務;
- 設定 Tailscale Serve 把 gateway 與 bridge 掛在 HTTPS 下;
- 最後**印出你要填進 iPhone 的 Host / Port / Token**。

---

## 4. 在 iPhone 設定 Nuvaryn app

1. 從 App Store 安裝 **Nuvaryn**,走完首次導引(可先按「試試示範模式」認識 Iris)。
2. 右上角 ⚙️ 設定 → **Gateway**:
   - Host:腳本印出的 MagicDNS 名稱(例如 `mac-mini.tail1234.ts.net`)
   - Port:`443`
   - 使用 TLS:**開**
   - 金鑰 → Gateway Token:腳本印出的 token
3. 回到聊天頁按「**連線**」。第一次會出現 🔐 配對訊息,內含一組 request ID。
4. 回到 Mac mini 終端機核准這支手機(**只需做一次**):
   ```bash
   openclaw devices list              # 看到 Pending 的 request id
   openclaw devices approve <request-id>
   ```
   > 注意:待核准清單會在 gateway 重啟時清空,看到 ID 就盡快核准。
5. 再按一次「連線」→ 綠燈「已連線」。跟 Iris 打個招呼吧。

---

## 5. 選用:本地離線模型(Ollama)

在 Mac mini 上:

```bash
curl -fsSL https://ollama.com/install.sh | sh        # 或從 ollama.com 下載 app
ollama pull qwen3:14b                                 # 約 9 GB,18 GB RAM 機器的甜蜜點
echo ollama-local | openclaw models auth paste-api-key --provider ollama
```

然後把模型加進 OpenClaw 的清單(`~/.openclaw/openclaw.json` → `agents.defaults.models` 加入 `"ollama/qwen3:14b": {"alias": "Local Qwen"}`)並重啟 gateway。
app 的模型選單會出現「Local Qwen」。

> **誠實的限制**:目前版本的 OpenClaw 對 Ollama 模型**不會注入人格設定(系統提示)**,因此本地模型不會自稱 Iris、也不會用工具(如查天氣)。
> 這是 OpenClaw 的已知問題([#74579](https://github.com/openclaw/openclaw/issues/74579)),請把本地模型當作「斷網備援」,日常請用雲端模型。

---

## 6. 驗證與疑難排解

| 症狀 | 原因 / 處理 |
|---|---|
| `origin not allowed` | `gateway.controlUi.allowedOrigins` 缺 `https://<MagicDNS>`。重新執行 `setup-host.sh`,或手動加入後重啟 gateway。 |
| `control ui requires device identity` | 你用的是舊版 app 或非 TLS 連線。請用 Port 443 + TLS 開。 |
| `pairing required` 一直出現 | 還沒核准,或核准前 gateway 重啟了。`openclaw devices list` 取得新 ID 再 approve。 |
| 連上了但**沒聲音**,且每句都變成女聲 | 伺服器語音取不到 → app 退回 iPhone 內建語音。檢查 bridge:`curl -s -o /dev/null -w "%{http_code}" https://<MagicDNS>/bridge/tts?path=x` 應回 `404`(服務活著);`000` 代表 bridge 掛了 → `launchctl kickstart -k gui/$(id -u)/com.nuvaryn.bridge`。 |
| 模型回 `402` / `429` | 402 = OpenRouter 未儲值;429 = 免費配額用盡或該 key 無此模型權限(Google 免費層只有 Flash,沒有 Pro)。 |
| 本地模型 `Auto-compaction could not recover` | `agents.defaults.compaction.reserveTokensFloor` 太大(對 33k 視窗模型致命)。腳本已設 6000。也可在 app 按 ✏️ 開新對話。 |
| 回覆變成「Audio reply」 | 伺服器端自動 TTS 開著。腳本已把 `tts.auto` 設為 off。 |
| Mac mini 重開機後 app 連不上 | gateway 與 bridge 都是 launchd 服務會自動起來;Tailscale Serve 設定也會保留。若仍不行,重跑 `setup-host.sh`。 |

完成!接著請看 [使用說明](user-guide.md)。
