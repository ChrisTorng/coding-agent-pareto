# 2026-10-30 首次雲端執行結果

**實際完成兩張 AA v2.0 參考圖；正式平台成本 Pareto 雙圖尚未完成。**

本次 Python 在雲端執行，未操作使用者 Windows。`functions.exec` 呼叫 `exec_command`，實際輸出 `2`；Python 3.12.14、matplotlib 3.10.8、Pillow 12.3.0。封裝 manifest 33 檔案的長度與 SHA-256 全數一致。原始 10/28 驗證程式通過 104 列、48 點與 51 筆來源對照；這只適用歷史 Intelligence Index v4.3.2。

## 本次產物

- Copilot：15 個當日核實的模型／effort 點；其中僅 Fusion Max 的能力成績來自 Copilot harness。
- Kiro：4 個當日核實的 Claude Code 跨 harness 參考點；Fable 為 Enterprise 限定。
- 兩張圖均為 Coding Agent Index v2.0，X 軸為 **AA API USD/task**，黑線為所選資料的 **AA API 參考前緣**。
- 所有 `platform_cost_task` 保持 null、`formal_frontier_eligible=false`。兩張圖均明示 REFERENCE ONLY。不是正式平台帳單、正式平台成本前緣或 Kiro 原生測試。
- 排除中國供應商與 Auto；未核實的 Fusion Standard/High、non-reasoning 可用性、Argon 衝突資料保存在 JSON/CSV，未填造能力或成本。
- 舊版 CSV 104 列及歷史 PNG/SVG 保留；新欄位獨立保存於 v2 目錄，避免將兩種指標混為同欄位。

## 原程式沿用與重現

原 `plot_copilot_pareto.py` 的 `plot` 增加可選 config，沿用原 Point、pairwise dominance、雙線性面板、放大來源框、同模型 effort 細線及 label_points 避讓。歷史 CLI 仍使用舊版本的日期與欄位防護。新增 `run_coding_v2.py` 將核實資料寫為新 CSV/JSON，呼叫同一個 plot。不是另造簡化散點圖。

```text
python copilot_pareto/run_coding_v2.py
```

此入口重現 **2026-10-30 凍結參考資料**，不會自動抓取新日期。以後先查核來源、合併資料、更新 snapshot_date 與必要欄位，再執行；不可只將日期改新。驗證包括獨立排序掃描前緣與原 pairwise 計算比對、版本、空值保護、唯一鍵、標籤重疊／裁切、PNG 解碼、PNG/SVG SHA-256 與實際目視圖面。Copilot 15 個標籤、Kiro 4 個標籤，均無重疊與裁切。

## 成本與資料缺口

Copilot 正式任務成本應為逐 request、逐底層模型、逐 context tier 的四類 token 用量乘相應 USD/1M 單價後加總，再除任務數。AI Credits = USD × 100。Fusion 促銷須依實際適用的底層模型計費；未有分解資料，不能將 AA API cost 直接乘 0.7。

Kiro 正式任務 Credits 需要該任務的可核實計費用量與適用 multiplier/context tier；倍率本身不能當絕對任務 Credits。跨 harness 的任務 token 用量也不能冒充 Kiro 原生用量。

目前仍缺 Fusion Standard/High 的相容 v2.0 成績、各模型四類 token 與 request context tier 分解、Fusion 底層模型分解、Kiro 任務 Credits。測試日期未公布時 `measured_at=null`；checked_at 是查核日，不能當測試日。頁面顯示總 tokens 為四捨五入，不反推精確分類。

Argon 在 `antigravity-cli-vs-grok-build` 顯示 $5.86，較新的 `antigravity-cli-vs-github-copilot` 顯示 $11.73；保留兩值衝突，這次不畫。Carbon 的 AA 資料另存，但當次 GitHub 支援表未列出，未畫入主圖，不能當 Argon 後繼者直接取代。

## 本次監測範圍與基準限制

已重新讀取 GitHub 支援表、模型費率與 Fusion 文件，Kiro Available models、Overview、Models changelog，以及 AA 五種 harness 比較頁。Fusion 付費 30% 促銷仍列至 11/30；Kiro 最新 changelog 為 10/23。不因舊資料缺完整全文基準就宣稱完成歷史逐欄全文 diff；沒有將舊快照誤標為當次完整 HTML。排程以既有 ID 更新，避免重複建立，保留其他排程。

## 模型使用原則的證據界線

本次不依參考圖提出平台成本排名。日常／成本敏感工作可將 Terra、Luna 或 Haiku 作為本機任務集的候選測試組；複雜重構與長時間 Agent 任務可測試 Sol、Opus 或 Fusion，但仍應比較各平台實際成功率與 Credits。高可靠度驗證採獨立測試、建置與審查；這些是待測工作流程，並非本次跨 harness 圖可證明的最佳選型。Kiro GPT-5.6 與圖上的 GPT-6/6.1 不同，不能沿用分數。

## 官方來源

- https://artificialanalysis.ai/agents/coding-agents?routers=true
- https://artificialanalysis.ai/agents/coding-agents/comparisons/codex-vs-github-copilot
- https://artificialanalysis.ai/agents/coding-agents/comparisons/claude-code-vs-github-copilot
- https://artificialanalysis.ai/agents/coding-agents/comparisons/antigravity-sdk-vs-github-copilot
- https://artificialanalysis.ai/agents/coding-agents/comparisons/antigravity-cli-vs-github-copilot
- https://artificialanalysis.ai/agents/coding-agents/comparisons/antigravity-cli-vs-grok-build
- https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing
- https://docs.github.com/en/copilot/reference/ai-models/supported-models
- https://docs.github.com/en/copilot/concepts/models/copilot-fusion
- https://kiro.dev/docs/models/
- https://kiro.dev/docs/models/available-models/
- https://kiro.dev/changelog/models/
