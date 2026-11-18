# Copilot / Kiro AA Coding Agent Index v2.1 — 2026-11-18

本版**沿用原 `copilot_pareto/plot_copilot_pareto.py`** 的 `Point`、pairwise Pareto、雙面板線性 X 軸、來源框、effort 細線、標籤避讓。`run_coding_v21.py` 只是讀取新版已核實 CSV 並呼叫同一繪圖器，**不是新的散佈圖實作**。原 104 列歷史 CSV、v2.0 資料及全部歷史 PNG/SVG 均保留。

## 本次產物／執行

```bash
python copilot_pareto/run_coding_v21.py
```

- `coding_agent_data_2026-11-18.csv/json`：**60 列**（兩平台的 AA v2.1 評測資料和待補項目），包含原生 Harness、模型、effort、Index、三分項、API Cost per Task、粗略總 Token、來源、版本與缺失原因。四種 Token 分項是空值，因沒有逐項可信資料；`measured_at` 未公布也留空。
- `copilot_coding_reference_2026-11-18_linear.png/svg`：25 個 Copilot 支援模型／effort 的**跨 Harness AA API 參考前緣**。沒有 Copilot 平台 v2.1 原生評測的推論。已核實前一代直系後繼者的行保留但排除主圖。
- `kiro_coding_reference_2026-11-18_linear.png/svg`：5 個 Kiro 已支援模型（Opus、Sonnet、Fable 5.1、Haiku 及 Grok）的**跨 Harness AA API 參考前緣**，不等於 Kiro 原生成功率／Credits。
- `platform_rates_2026-11-18.csv`：**33 筆**已查證的 Copilot 四類每百萬 Token 價格及 Kiro 依 context tier 的 Credit Multiplier。未分開收取的欄位留空。
- `platform_task_cost_layer_2026-11-18.csv`：**80 筆**模型、effort、context tier 與官方單價／倍率的對照；`actual_platform_task_credits` 一律空白、`is_formal_frontier_eligible=False`，不得據此宣稱正式成本 Pareto。
- `validation_2026-11-18.json`：沿用原繪圖器 Pareto/標籤/兩軸驗證與 PNG/SVG SHA-256。

## 指標及來源

2026/11/18 AA 現行 **Coding Agent Index v2.1** = FrontierCode-AA 2.0、Terminal-Bench 4.1、SWE-Atlas-QnA-AA 等權重。**絕不與舊 v2.0 或 Intelligence Index 混算**。官方網站無公開 API，資料取自當日可核實的兩兩比較表，當日手工轉錄並在 CSV 保存每列來源：

- https://artificialanalysis.ai/agents/coding-agents
- https://artificialanalysis.ai/methodology/coding-agents-benchmarking/
- https://artificialanalysis.ai/agents/coding-agents/comparisons/claude-code-vs-codex
- https://artificialanalysis.ai/agents/coding-agents/comparisons/antigravity-cli-vs-claude-code
- https://artificialanalysis.ai/agents/coding-agents/comparisons/antigravity-cli-vs-grok-build
- https://docs.github.com/en/copilot/reference/ai-models/supported-models
- https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing
- https://docs.github.com/en/copilot/concepts/models/copilot-fusion
- https://kiro.dev/docs/models/available-models/

## 費用定義與無法正式產圖的界線

對 Copilot，理論上每個被實際計費的 request／底層模型／context tier 必須分開計算：

`USD_task = Σ_requests [(U×P_input + C×P_cached + W×P_cache_write + O×P_output) / 1,000,000]`，`AI Credits = USD_task / 0.01`。

U/C/W/O 必須是該模型該次請求的**實際 Token 明細**。尤其 Fusion Standard/High/Max 可選多模型、多次呼叫，且目前付費方案模型費用優惠至 **2026/11/30**；不能直接將 AA API 任務成本乘 0.7。Copilot 一般/Long Context 費率已在 `platform_rates` 分層保存。

Kiro 的倍率**不是絕對任務 Credits，也不是美元成本**。Kiro 的各模型倍率見 `platform_rates`，部分依 100K／200K／272K 分層。只有取得 Kiro 真實已計費任務使用量，才能算每任務 Credits 和正式成本前緣。AA Claude Code、Codex、Antigravity、Grok Build 的 API Token 紀錄不能充當 Kiro 原生任務用量。

**促銷查核（截至 11/18，須以官方實際公告為準）**：Fusion 付費 30% 至 11/30；Gemini Argon／Carbon 促銷價至 12/1；Gemini 3.8 Flash 至 12/31；MAI Code 2／Flash 至 2027/5/17（未有相容 AA v2.1，故不畫）。預定期滿不等於已變價。

**待補**：Fusion v2.1 三努力量原生資料、四類 per-request Token、Fusion 底層模型分解、Kiro-native task Credits、Kiro GPT-5.6 Sol/Terra/Luna 相容 v2.1 benchmark。這些模型留待補列；不以零分、零成本冒充測量。

**篩選**：排除中國模型及 Auto；保留 Fable 5.1／GPT-6 Astra／GPT-6.1 Sol 的追溯資料，但 Copilot 參考主圖視為已有直接後繼者而排除。Kiro Fable 5.1 為 Enterprise 限定，Fable 5.2 未列入 Kiro。來源的「Default Fallback」保持原樣，表示受 fallback 影響，不能等同純模型評測。當日只是查核日期，不代表評測當日。

## 參考圖閱讀與實務模型選用（非平台 Credits 排名）

Copilot 日常與成本敏感，可先測 GPT-6.2 Sol（medium/high）及 Gemini Hydrogen；複雜重構可比較 Astra、Fable 5.2 與 Fusion，但 Fusion 的 v2.1 成績尚待補齊。Kiro 成本敏感可先測 Haiku 5.5、GPT-5.6 Luna/Terra（無相容 v2.1 評測）；複雜任務可以對比 Opus/Sonnet。長時間 Agent 任務、高可靠度驗證需對同一真實工作負載的成功率、token/credits、建置與測試結果做平台原生比較，不應由這些跨 Harness 點推斷實際排名。

## 2026-11-18 漏項補正：Terra、Luna 與 Fusion

- AA v2.1 Codex **GPT-6 Luna (max)**：26 分，FrontierCode-AA 2.0＝24、Terminal-Bench 4.1＝15、SWE-Atlas-QnA-AA＝38，AA API cost/task US$0.19、10.1M tokens。原 v2.1 收錄漏掉，已補入 Copilot 的 24 個參考點；Kiro 不支援，僅保留排除列。官方來源：https://artificialanalysis.ai/agents/coding-agents/comparisons/codex-vs-devin-fusion-cli 。
- **GPT-6.1 Terra**：公開 v2.1 Codex 目前僅核實 max（49 分，US$1.53/task）；v2.0 的 low/medium/high/xhigh/max 數據保留在原版，但分數不可與 v2.1 混算。
- **Copilot Fusion Max**：AA **v2.0 GitHub Copilot 原生 Harness** 60 分、US$5.59/task（AA API cost）；不是 v2.1、也不是 Copilot 平台真實 Credits，不能放在 v2.1 前緣。Standard / High 尚未核實分數。
- **Devin Fusion CLI**：AA v2.1 Claude Opus 5.5 Max + GPT-6 Luna High，58 分、US$8.75/task，**不同產品**、不等於 Copilot Fusion。
- 新增 `coverage_v20_vs_v21_2026-11-18.csv` 對齊版本資料缺口，及 `fusion_harness_comparison_2026-11-18.csv` 防止將不同產品與指標混淆；兩份 CSV 都不進入 v2.1 前緣。

圖表來源的 X 軸仍只有 AA API 成本，不是 GitHub Copilot／Kiro 實際平台成本。

- **GPT-6.1 Sol (max)**：11/18 GitHub 官方仍列為 GA，AA v2.1 Codex 52 分、API US$1.51/task；因 6.2 Sol max 49 分、1.22 美元未支配此舊款，不能光按新版本號排除。已恢復到 v2.1 參考主圖。來源：https://docs.github.com/en/copilot/reference/ai-models/supported-models 、https://artificialanalysis.ai/agents/coding-agents/comparisons/codex-vs-devin-fusion-cli 。
