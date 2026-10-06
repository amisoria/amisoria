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
| RPC 方法 | `chat.startup`、`chat.send`、`sessions.messages.subscribe`、`sessions.patch`、`models.list`、`tts.status`、`tts.providers`、`tts.setProvider`、`tts.convert`、`config.get`、`config.patch`、`health` |
| 串流事件 | `session.message`（助理的串流內容可能在回覆中途被整段改寫，App 已處理） |
| 檔案（透過 bridge） | TTS 輸出在 `~/.openclaw/media/`（2026.9.1 起）或 `/private/tmp/openclaw/`（更早版本） |
| 主機端 | 用 `openclaw devices approve` 配對；走 Tailscale Serve 時需要 `gateway.tailscale.mode: "off"` 與 `gateway.trustedProxies` |

未來若有版本改名或移除上述方法，App 會顯示紅點並寫出缺少的方法，本頁也會說明處理方式。

## 各版本狀態

| OpenClaw | 狀態 | Amisoria | 備註 |
|---|---|---|---|
| **2026.9.8** | **已驗證** | 1.4 | 在 Mac mini（Node 26）上驗證（2026-10-05）：從 9.6 原地升級（`npm i -g openclaw@2026.9.8` 加 `openclaw doctor --fix`），設定維持有效，API 金鑰與模型清單都保留；App 用到的每個 Gateway 方法都有回應；十多輪的免持對話（伺服器語音、對嘴、插話打斷、上網查詢）通過。**即時串流需要 Amisoria 1.4**（9.7 改了串流格式，見下一列）；用 1.3 的話回覆要整段寫完才會出現。從 App 寫入新 API 金鑰這個動作沒有在這個版本重跑。 |
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
