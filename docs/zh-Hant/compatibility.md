# OpenClaw 版本相容性

OpenClaw 一個月會出好幾版，Amisoria **不會**每一版都追。我們的做法是：

- **App 只依賴 Gateway 一小塊穩定的介面**（見下表），不依賴版本號。只要新版沒動到這塊介面，App 就照常運作。
- **一次只完整驗證一個版本**：語音、對嘴、模型切換、寫入 API 金鑰、裝置配對全部跑過才標為「已驗證」。新版本上線後先等約一週（讓社群先踩雷），再進行測試。
- **App 會告訴你目前的處境。** Amisoria 1.3 起，「連線設定」最下方會顯示 Gateway 版本和一個圓點：綠色＝已驗證；橘色＝尚未測試，但 App 需要的功能都在；紅色＝缺少 App 會呼叫的功能（會寫出原因）。更早的 App 版本只會直接嘗試連線。

## Amisoria 實際用到的東西

| 介面 | 內容 |
|---|---|
| WebSocket 協定 | `4`（連線握手時檢查） |
| 連線參數 | control-ui 型客戶端、必須帶 `client.buildId`（2026.9.1 起）、Ed25519 裝置身分 v2、Gateway token |
| RPC 方法 | `chat.startup`、`chat.send`、`sessions.messages.subscribe`、`sessions.patch`、`models.list`、`tts.status`、`tts.providers`、`tts.convert`（Amisoria 1.5 起每次請求帶 `provider` 與 `voiceId`；1.4.x 改在連線時呼叫 `tts.setProvider`）、`config.get`、`config.patch`、`health` |
| 串流事件 | `session.message`（助理的串流內容可能在回覆中途被整段改寫，App 已處理） |
| 檔案（透過 bridge） | TTS 輸出在 `~/.openclaw/media/`（2026.9.1 起）或 `/private/tmp/openclaw/`（更早版本） |
| 主機端 | 用 `openclaw devices approve` 配對；走 Tailscale Serve 時需要 `gateway.tailscale.mode: "off"` 與 `gateway.trustedProxies` |

未來若有版本改名或移除上述方法，App 會顯示紅點並寫出缺少的方法，本頁也會說明處理方式。

## 已知問題

### Microsoft 語音回應 403（2026-10-12 起）

Microsoft 在 2026-10-12 更換了 Edge「大聲朗讀」的端點。OpenClaw 到 **2026.10.9** 為止（目前每一版都是；10.4 由一位 Linux 使用者在 [issue #1](https://github.com/amisoria/amisoria/issues/1) 確認）內建的 `node-edge-tts` 1.2.10 仍連舊主機，所以用 Microsoft 供應商的每一次 `tts.convert` 都失敗：`Unexpected server response: 403`。App 裡聽到的會變成 iPhone 內建語音。Amisoria 1.4 在這種情況下連英文回覆都用中文裝置語音念；**1.4.1（2026-10-13 上架）** 會用正確語言退回，並在對話中顯示提示讓你知道伺服器語音失敗了。

在 OpenClaw 推出含新版 `node-edge-tts` 的版本之前，可以把內建的那份換成 1.2.11（新端點、API 相同）。在 Mac 上：

```bash
cd "$(npm root -g)/openclaw"
cp -a node_modules/node-edge-tts ~/node-edge-tts-backup
npm pack node-edge-tts@1.2.11 --silent && tar xzf node-edge-tts-1.2.11.tgz
rm -rf node_modules/node-edge-tts && mv package node_modules/node-edge-tts && rm node-edge-tts-1.2.11.tgz
openclaw gateway restart --force
```

2026-10-13 在 OpenClaw 2026.9.8 上驗證（zh-TW 與 en-US 語音，每句 0.5–0.8 秒），2026-10-31 在 2026.10.9 上再次驗證；另有使用者在 2026.10.4（Linux）上驗證（453 次合成，中位數約 0.5 秒）。下一次 `npm i -g openclaw@…` 會把這個修補蓋掉，升級後請再試一次語音；要還原就把備份資料夾放回去再重啟。之後若語音清單變成空的，表示 Gateway 自己抓語音清單的那條路（仍連舊主機）也壞了，請到 Issues 告訴我們。

### 「speech provider microsoft is not registered」

Microsoft 語音需要**兩個**開關：`tts.providers.microsoft.enabled` **和** `plugins.entries.microsoft.enabled`。外掛那個沒開的話，Gateway 會用 `Invalid provider` 拒絕 App 送的 `tts.setProvider("microsoft")`，之後每次合成都走 Gateway 當時停留的供應商（常常是 ElevenLabs，回「not configured」），App 就退回裝置語音。`setup-host.sh` 會開這個外掛；手動安裝請自己設定，並**完整重啟** Gateway（設定熱載入不會載入外掛）。Amisoria 1.4.x 只在「連線設定 → 語音引擎」下方用小字顯示切換被拒絕。1.5 不再改動主機的供應商——供應商隨每次請求送出——並在對話裡顯示 Gateway 的原因，加一行指向這個設定的提示。

### Tailscale 託管模式會擋掉 `/bridge`

若 `gateway.tailscale.mode` 是 `"serve"`（OpenClaw 官方文件建議的值），OpenClaw 會自己在 443 跑一個*前景* `tailscale serve`，bridge 就加不進去：`tailscale serve --set-path=/bridge …` 會回 `foreground listener already exists for port 443`。沒有 bridge 時，`/bridge/tts?…` 會落到 Gateway，Gateway 回 **HTTP 200 的 Control UI 網頁**，App 拿不到音檔、退回裝置語音，手機上看不出原因。Amisoria 需要手動管理的路由：

```jsonc
// openclaw.json
"gateway": { "tailscale": { "mode": "off" }, "trustedProxies": ["127.0.0.1", "::1"] }
```

```bash
# 重啟 Gateway 之後：
tailscale serve --bg --https=443 http://127.0.0.1:18789
tailscale serve --bg --https=443 --set-path=/bridge http://127.0.0.1:18790
```

**陷阱：**改 `gateway.tailscale.mode` 需要重啟 Gateway，而 OpenClaw 可能把重啟**延後**到進行中的代理回合結束——有使用者等了約 30 分鐘，`openclaw gateway restart --force` 也沒有跳過等待。舊路由拆掉、新路由還沒起來的期間，手機連不上。請在沒有任務進行時做。從手機端檢查路由：`curl -s -o /dev/null -w "%{content_type}" "https://<主機>/bridge/tts?path=x"` 印出 `text/html` 就表示 bridge *不在*；bridge 活著會回 404、沒有網頁。

## 各版本狀態

| OpenClaw | 狀態 | Amisoria | 備註 |
|---|---|---|---|
| **2026.10.9** | **已驗證** | 1.5.1 | 2026-10-31 在 Mac mini 上驗證（從 9.8 原地升級，Amisoria 1.5.1）：App 呼叫的每個方法都有回應，Microsoft 語音的 `tts.convert` 與經 Tailscale Serve 的 bridge 取檔都通過。**需要 Node 24.22.1 以上或 26.12.1 以上**（2026.10.6 起，因應 2026 年 10 月的 Node 安全性更新；舊 Node 下 gateway 會拒絕啟動）：`nvm install 26 && nvm alias default 26`，在新 Node 下重新安裝 OpenClaw（全域套件是跟著 Node 版本走的），再 `openclaw gateway install --force` 讓 launchd 服務改用新的 Node——其他寫死舊 Node 路徑的東西也要改（我們的 bridge LaunchAgent 就是）。**仍內建 `node-edge-tts` 1.2.10**，升級後要重做上面的 1.2.11 替換。`tts.convert` 多回傳一個 `voiceCompatible` 欄位（App 不使用）。`plugins.entries`、`gateway.tailscale.mode`、`trustedProxies` 與裝置配對都在升級後保留。App 內對 10.9 的綠燈要等下一版 Amisoria；1.5.1 顯示橘燈、方法齊全。 |
| 2026.10.6 – 2026.10.8 | 未測試 | — | 維護版（更新／復原流程、相依套件安全性修補）；更新說明已對照上面的介面檢查，沒有動到。10.6 開始要求新版 Node、並為慢速的雲端語音合成加上逾時；10.8 讓 Tailscale Serve 在 tailscaled 重啟後能恢復。已被 10.9 取代。 |
| 2026.10.4 | 可用（使用者回報） | 1.4.3 – 1.5 | 一位使用者在 **Linux** 主機上手動安裝後回報可用（[issue #1](https://github.com/amisoria/amisoria/issues/1)，2026-10-20）：語音、對嘴、插話、iPhone 與 iPad。同一位使用者後來在這台主機上跑 Amisoria 1.5（TestFlight build 13、14，與上架版相同）：AirPods 三種模式、「Gateway 預設」接本地 Piper（2026-10-26）。仍內建 `node-edge-tts` 1.2.10（Microsoft 403，照上面換成 1.2.11）。我們自己的主機還沒跑過，所以不標已驗證。App 呼叫的方法都有回應。 |
| **2026.9.8** | **已驗證** | 1.4 – 1.5.1 | Amisoria 1.5 與 1.5.1 都是在這個版本上開發與實機測試的（1.5：2026-10-23 ～ 10-27，供應商選單、每次請求帶 `provider`、兩句同時合成、藍牙耳機；1.5.1：2026-10-28 ～ 10-30，插話與重連修正，中文三輪、英文十句）。在 Mac mini（Node 26）上驗證（2026-10-05）：從 9.6 原地升級（`npm i -g openclaw@2026.9.8` 加 `openclaw doctor --fix`），設定維持有效，API 金鑰與模型清單都保留；App 用到的每個 Gateway 方法都有回應；十多輪的免持對話（伺服器語音、對嘴、插話打斷、上網查詢）通過。**即時串流需要 Amisoria 1.4**（9.7 改了串流格式，見下一列）；用 1.3 的話回覆要整段寫完才會出現。從 App 寫入新 API 金鑰這個動作沒有在這個版本重跑。 |
| 2026.9.7 | 未測試 | — | **改了即時回覆的串流方式。**`agent` 的 assistant 事件現在只送新增的文字（`data.delta`），不再每次送到目前為止的完整文字；協定版本仍然是 4。Amisoria 1.3（含）以前讀的是完整文字，所以在 9.7 以上，回覆可能要等模型整段寫完才顯示、才開始念，OpenClaw 的更新紀錄也寫明舊客戶端可能漏掉回覆文字。Amisoria 1.4 兩種格式都讀，並已在 2026.9.8 驗證（見上一列）；9.7 本身沒有跑過。使用 Amisoria 1.3 的話請留在 2026.9.6。另外移除了 Tasks／TaskFlow 面板與 API（我們沒用）；手動升級後請執行 `openclaw doctor --fix`。 |
| 2026.9.6 | 已驗證 | 1.3 – 1.4 | 在全新 Mac mini（Node 26）上完整跑過（2026-09-27）：文字、伺服器語音＋對嘴、麥克風、角色切換、模型切換、寫入 API 金鑰、10 句長對話。移除了 `sessions.compaction.*`（我們沒用）；設定錯誤現在會引導執行 `openclaw doctor --fix`。**全新安裝的第一句回覆會明顯比較慢**（代理要先跑開機儀式，Gateway 也可能還在下載模型目錄），多等一下就好，只有第一次。**退役了 `agents.defaults.compaction.reserveTokensFloor`**，檔案裡若還有會被拒絕（設定無效 → CLI 不執行、App 套用金鑰失敗、Gateway 重啟不了）；2026-09-28 之後的 `setup-host.sh` 會自動移除，舊版腳本會寫入它，請執行 `openclaw doctor --fix` 或重跑腳本。OpenAI 模型改走 codex 外掛，串流結束時會用 `replace:true` 把完整回覆再送一次；Amisoria 1.3 已處理，1.2 會把這種回覆顯示並念兩次。 |
| 2026.9.5 | 未測試 | — | 已看過更新紀錄，沒有動到上述介面。升級注意：9.5 把舊的配對／對話資料修復改成要手動執行 `openclaw doctor --fix`，升級後若 Gateway 提示有待修復項目，跑一次即可。 |
| 2026.9.4 | 未測試 | — | 已看過更新紀錄，沒有動到上述介面。 |
| 2026.9.3 | 未測試 | — | **主機端重大變更：**需要 Node 24.16 以上（24.x）或 Node 26.1 以上（建議 26）。**先升 Node 再升 OpenClaw**，否則 SQLite 文字截斷可能弄壞對話紀錄。 |
| 2026.9.2 | 未測試 | — | 新增大型對話啟動的 WebSocket 壓縮，我們要實際測過才會標為已驗證。 |
| 2026.9.1 | 已驗證 | 1.1 – 1.2 | 主機腳本與安裝指南最初針對的版本。Amisoria 1.3 只在 2026.9.6 上完整驗證過，沒有回頭在 9.1 重跑；1.3 沒有依賴新版 Gateway 才有的東西，預期可正常使用。從 2026.7 升上來的坑都記在[安裝指南](install-mac-mini.md#升級-openclaw-時的注意事項)。 |
| 2026.7.x | 1.0 可用 | 1.0 | Amisoria 1.0 是在這個版本上開發的。1.1 開始送 `client.buildId` 後沒有再回頭測。 |

「未測試」就是字面意思，不代表壞掉。如果你在那些版本上跑得動（或跑不動），到 [Issues](https://github.com/amisoria/amisoria/issues) 留一句話，對所有人都有幫助。

## 升級步驟

1. 先看上表該版本那一列，以及[升級注意事項](install-mac-mini.md#升級-openclaw-時的注意事項)。
2. 備份 `~/.openclaw/openclaw.json`。新版會把某些鍵退役（2026.9.6：`agents.defaults.compaction.reserveTokensFloor`、`gateway.controlUi.allowInsecureAuth`），退役的鍵留在檔案裡會讓設定無效、Gateway 起不來。用 `openclaw config validate` 檢查；不要手動補回。
3. 該版本若要求新 Node，先升 Node，再 `npm i -g openclaw@<版本>`。
4. 升完先在前景跑一次 `openclaw gateway`，看第一頁輸出。launchd 服務把 stderr 丟到 `/dev/null`，設定錯誤在服務模式下只會看到一直重啟。
5. 重新執行 `host/setup-host.sh`，它會補回 App 依賴的設定並更新 bridge。
6. 打開 Amisoria → 連線設定，看 Gateway 版本的圓點顏色。

## 一段話說明政策

「已驗證」只有上表標示的版本，其餘都是盡力支援。我們自己的主機固定在最新的已驗證版本；新版本上線約一週後測試，完整流程通過就把「已驗證」往前移。我們不會為舊版 OpenClaw 回頭修補；若哪一版真的動到 App 依賴的介面，會在本頁明說。
