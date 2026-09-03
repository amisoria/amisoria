# 人設與提示詞指南（踩坑紀錄）

Amisoria 把 OpenClaw 的回覆**唸出來、配上 3D 角色的嘴型與表情**。文字聊天無所謂的小毛病，到了語音就會變成「唸出一串網址」或「先用英文自言自語再回答」。這一頁整理我們實際踩過的坑，以及對應的 **prompt 層解法**——全部寫在 `~/.openclaw/workspace/AGENTS.md`（OpenClaw 的人設檔）即可，不需要改程式。

> 懶人做法：`host/setup-host.sh` 會自動把 [`host/workspace/AMISORIA-RULES.md`](../../host/workspace/AMISORIA-RULES.md) 的內容追加到你的 `AGENTS.md`（有標記、可重複執行不會重複貼）。手動的話直接把該檔內容貼到 `AGENTS.md` 末尾。

## 坑 1：模型把「內部思考」寫進回答（Gemini 尤其常見）

**現象**：回覆開頭出現一段英文第三人稱自述——「Glen is back. He's asking where I'm going. I'll respond warmly.」——然後才接中文回答。語音會把這段英文整個唸出來。

**原因**：`gemini-3-flash-preview` 這類 thinking 模型偶爾把盤算內容直接放進正文。OpenClaw 的管線其實把思考區塊分開處理了，但這種情況思考就在正文裡，程式層攔不到。

**解法**（AGENTS.md）：
```
- 直接輸出要對使用者說的話。絕對不要先輸出任何內部思考、計畫或第三人稱敘述
  （例如 "Glen is back. He is asking… I will respond warmly."）——一個字都不能出現。
- 一律以使用者當前使用的語言開場；不要在回覆開頭夾雜另一種語言的自述。
```
實測 prompt 層堵法有效；若仍偶發，換成非 preview 的模型版本。

## 坑 2：Markdown 被唸出來

**現象**：語音唸出「星星星星」「井字號」，或字幕出現 `**粗體**`、表格符號。

**解法**：App 已會剝除 markdown，但**最乾淨的是從源頭禁用**：
```
Do not use markdown formatting (no **bold**, no tables; lists are fine as plain lines)
— replies are displayed as plain text and spoken aloud.
```

## 坑 3：網址與引用標記

**現象**：唸出「https 冒號 斜線 斜線 order 點 nidin 點 shop…」；或字幕出現 `⍰cite🚢turn7search2`（OpenAI 網頁搜尋的內部引用 token，用私有區 Unicode 包住，iOS 畫成問號和船）。

**解法**：App 端已把網址從語音剔除、引用 token 整段剝掉；prompt 層再補一條讓來源更好看：
```
Do not paste raw URLs into sentences that will be read aloud. If you must cite a
source, put the site name in parentheses at the end of the sentence, e.g. "(example.com)".
```

## 坑 4：語言混用

**現象**：一句話裡中英夾雜，App 的分句語言偵測會在句中切換聲音，聽起來斷裂。

**解法**：
```
Always reply in the language of the user's latest message. Do not mix languages
in one sentence unless the user does. If the user's language is ambiguous
(a bare emoji or a name), keep the language of the previous turn.
```

## 坑 5：表情符號

**現象**：語音把 🙂 唸成「微笑的臉」，或角色全程一號表情。

**解法**：Amisoria 把回覆裡的 emoji **抽出來當成表情播放**（不唸、不顯示）。在 AGENTS.md 告訴模型這件事和對應表（🙂😊 溫暖、🤔 思考、😌 安心、😅 小失誤、😮 驚訝、🥺 關心、😉 俏皮、😐 中性），並要求「一則回覆最多一個、放句首或句尾」。

## 坑 6：說自己「只是沒有感情的助理」

**現象**：問她下午要去哪，回「As an AI, I don't go anywhere」。

**解法**：在 AGENTS.md 開頭宣告身分：`YOU ARE IRIS — a warm, elegant, empathetic AI companion. Never say you are "an assistant without feelings".`

---

修改 `AGENTS.md` 後**不需要重啟 Gateway**，下一則訊息即生效。改動前請先備份（`cp AGENTS.md AGENTS.md.bak`）。
