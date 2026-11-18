> 2026-10-30 本次雲端重現：已產製 Copilot 15 點／Kiro 4 點 AA v2.0 **參考圖**，正式平台任務成本仍缺值。完整說明見 [v2/README.md](v2/README.md)。本次環境 Python 可用，舊環境失敗紀錄不適用本次。

# GitHub Copilot 模型／effort Pareto frontier

> **2026-10-30 新版規格狀態：** 已找回原始資料及程式；Copilot／Kiro 的 Coding Agent Index v2.0 正式雙圖尚未完成，缺可執行雲端專案與可核實的平台任務成本。以下為 10/28 Intelligence Index 歷史成果，不能作為新版指標排名。復原記錄與當日監測基準見 [monitor/recovery_2026-10-30.md](monitor/recovery_2026-10-30.md) 及 [結構化基準](monitor/baseline_2026-10-30.json)。

資料快照：**2026-10-28（Asia/Taipei）**。輸出：`copilot_model_pareto_2026-10-28_linear.png` 及同名 SVG。舊日期圖檔與來源快照保留。

排除 Auto；全成本圖、低成本放大圖的 **X 軸皆為線性**。每點標籤僅含模型／effort。黑色粗線與外圈標記代表 frontier；同模型各 effort 依 low → medium → high → xhigh → max，以同色細線連接，缺值不補點。左圖藍色虛線框精確對應右圖：X −0.012 至 0.85 USD/task，Y 20 至 60。

## 本次更新

- CSV **104 列**，重新查核 **51 筆** AA 模型／effort。主圖 **48 點**：43 點 published cost、5 點 Haiku provisional cost。
- GitHub 支援表列出 **28 個名稱**，其中 Grok 4.5 與 10 月 19 日生效淘汰公告衝突；依有明確日期的公告標為 retired、排除主圖，衝突留於快照。
- GPT-6.1 Terra 於 10 月 26 日加入 Copilot，取代主圖的 GPT-5.6 Terra。新 Terra 的 low／medium／high／xhigh／max 分數為 **36／41／44／45／48**，成本 **$0.05／0.10／0.13／0.19／0.40 per task**。non-reasoning（33、$0.11）保留 CSV，尚未確認可選取的 Copilot 對應設定。
- AA task cost 更新：Gemini 3.8 Flash medium／high 從 $0.93／1.24 改為 **$2.59／3.49**；Grok 4.7 low／high／xhigh 從 $1.25／2.73／3.74 改為 **$1.03／2.36／3.24**；Argon high 從 $1.99 改為 **$1.62**，仍為 53 分。其他當日查核既有分數與成本不變。這些成本變動不等於 Copilot token 單價變動。
- published-cost frontier 從 13 點增為 **17 點**。Terra low／medium／high／xhigh 入選，Sol low（42、$0.13）被 Terra high（44、$0.13）支配；Argon 因成本下降入選。Terra max 被 Sol medium（48、$0.21）支配。
- 納入 Haiku 暫定成本後仍為同一組 **17 點**。Haiku xhigh（41、$0.12）被 Terra medium（41、$0.10）支配，其他 effort 亦被支配。本次無額外暫定 frontier 虛線段，暫定點仍以菱形顯示。

## 欄位與代表性成本公式

Y 軸：**Artificial Analysis 完整 Intelligence Index v4.3.2**，包含 AA-Briefcase v1.1、GDPval-AA v2.1、AutomationBench-AA、Terminal-Bench 4.0、SciCode、Humanity's Last Exam、GDP.pdf、CritPt、AA-Omniscience、AA-LCR v1.1 十項評估。未以 Coding Agent Index 或單項 coding 分數代替。

X 軸：AA **Cost per Intelligence Index Task**，即依評估權重計算的平均任務成本。使用 AA 原始 task cost，另查核 Copilot input／cached input／cache write／output 單價。未以 blended price per million tokens 或 premium request multiplier 代替 task cost。

代表性公式（P 單位為 USD／1M tokens）：

```text
cost_eval = [
    uncached_input_tokens × P_input
  + cache_hit_tokens       × P_cached_input
  + cache_write_tokens     × P_cache_write
  + (reasoning_tokens + answer_tokens) × P_output
] / (1,000,000 × number_of_tasks)

cost_per_index_task = Σ (evaluation_weight × cost_eval)
representative AI credits/task = USD/task × 100
```

GitHub **1 AI credit = US$0.01**。例如 Terra high $0.13/task 約為 13 credits，僅為 AA workload 換算。實際 Copilot repo、harness、cache、context 與 token 組成不同，不能視為帳單預測。長 context 必須逐次 request 判斷門檻再計價，不能以平均 tokens 重算；公開明細不足時不補造成本。AA cache discount 可能四捨五入，Copilot cached input 以官方價格表為準。

| CSV 欄位 | 用途 |
| --- | --- |
| `model`, `effort` | 同模型不同 reasoning／effort 分開記錄 |
| `intelligence_index_v4_3_2` | 完整綜合指數 |
| `aa_cost_usd_task` | 公布 task cost；缺值保持空白 |
| `score_status`, `cost_status`, `fallback` | measured／estimated；published／provisional／pending；AA fallback |
| `copilot_*_per_m` | default-tier 四類 token 單價；不適用的 cache write 留空 |
| `included_main`, `exclusion_reason` | 是否畫入主圖與排除原因 |
| `availability_status`, `retirement_date` | 支援、預定淘汰、已淘汰或年繳例外 |
| `successor`, `suggested_alternative` | 直接產品後繼者、淘汰公告當時建議替代品，分別保存 |
| `snapshot_date`, `benchmark_checked_at`, `pricing_checked_at` | 快照日期與各資料實際查核日期 |
| `promotion_deadline`, `copilot_pricing_status`, `cost_note` | 促銷期限、範圍與成本限制 |
| `benchmark_source`, `pricing_source` | 原始 effort 頁與官方價格來源 |
| `audit_method`, `audit_source` | 本次使用模型頁、比較頁或搜尋索引的查核方式與網址 |

來源 JSON 保存當日 catalog、**41 筆 default／long-context 費率**、51 筆 AA 紀錄、逐點數字摘錄、促銷、生命週期與查核限制。已下架模型的歷史費率保留 CSV，價格查核日期留空；未重查的 benchmark 保留原查核日期。

## Pareto frontier

若另一點成本不高於它、分數不低於它，且至少一項嚴格更好，即被支配。同成本同分數的不同模型都保留。依公開四捨五入數字計算，細微差異不代表統計顯著；連線只是閱讀引導。

| Frontier 模型／effort | Index | USD/task |
| --- | ---: | ---: |
| GPT-6 Luna/low | 22 | 0.0045 |
| GPT-6 Luna/medium | 30 | 0.02 |
| GPT-6 Luna/high | 33 | 0.03 |
| GPT-6 Luna/xhigh | 35 | 0.04 |
| GPT-6.1 Terra/low | 36 | 0.05 |
| GPT-6 Luna/max | 38 | 0.07 |
| GPT-6.1 Terra/medium | 41 | 0.10 |
| GPT-6.1 Terra/high | 44 | 0.13 |
| GPT-6.1 Terra/xhigh | 45 | 0.19 |
| GPT-6.1 Sol/medium | 48 | 0.21 |
| GPT-6.1 Sol/high | 50 | 0.32 |
| GPT-6.1 Sol/xhigh | 51 | 0.39 |
| GPT-6.1 Sol/max | 52 | 0.72 |
| Gemini 4 Argon/high | 53 | 1.62 |
| Claude Opus 5.5/high | 54 | 1.82 |
| Claude Opus 5.5/xhigh | 56 | 3.46 |
| Claude Opus 5.5/max | 58 | 5.98 |

這是 **Copilot 現行代表性子集合** 的 frontier；AA 全站另有 Copilot 不支援的模型，因此與 AA 新聞文章只強調 Terra low／medium 的全站 frontier 不矛盾。

Haiku low／medium／high／xhigh／max 分數為 29／34／38／41／43，暫定成本 $0.02／0.05／0.08／0.12／0.21。AA 的 10 月 7 日文章截至本次仍明示未納入 >100K input 五倍費率。五點皆為 provisional，不能移除 published-cost 實線 frontier 的點。腳本另計含暫定成本的 frontier，只有新增段才畫橘色虛線。

## Copilot 代表性單價

default tier，USD／1M tokens；cache write 不適用以 — 表示。

| 模型 | Input | Cached input | Cache write | Output |
| --- | ---: | ---: | ---: | ---: |
| GPT-6 Luna | 0.10 | 0.01 | 0.125 | 0.50 |
| GPT-6.1 Terra | 1.00 | 0.05 | 1.25 | 5.00 |
| GPT-6.1 Sol | 2.00 | 0.10 | 2.50 | 10.00 |
| GPT-6 Astra | 10.00 | 1.00 | 12.50 | 50.00 |
| Claude Haiku 5.5 | 0.10 | 0.01 | 0.125 | 0.50 |
| Claude Sonnet 5.5 | 2.00 | 0.10 | 2.50 | 10.00 |
| Claude Opus 5.5 | 4.00 | 0.20 | 5.00 | 20.00 |
| Claude Fable 5.1 | 10.00 | 0.25 | 12.50 | 50.00 |
| Gemini 3.8 Flash | 0.75 | 0.075 | — | 3.75 |
| Gemini 4 Argon | 2.00 | 0.10 | — | 10.00 |
| Grok 4.7 | 2.00 | 0.50 | — | 6.00 |
| Kimi K3 | 3.00 | 0.30 | — | 15.00 |

Haiku >100K input：0.50／0.05／0.625／2.50。Terra 6.1 >272K：2.00／0.10／2.50／7.50。其餘 GPT-6 系列 >272K、Grok >200K 也有高階費率，詳見來源 JSON。

## 促銷、淘汰與代表性篩選

- Gemini 3.8 Flash 促銷至 **2026-12-31**（through）；Argon 至 **2026-12-01**（until，當天應重查）。GitHub 價格與期限本次未變。
- GPT-5.6 Sol provider 促銷至少至 **2026-11-21**，保留於 CSV；這不是 GitHub 承諾的 Copilot 期限。其他主圖模型未見官方促銷截止日，留空不保證永久價格。
- 不沿用舊快照 Argon $3.98 的促銷後情境值：當日 AA task cost 已變、缺逐任務 token 明細，不重新推算未來帳單。
- **10 月 19 日已淘汰六款**：Gemini 3.7 Flash、GPT-5.5、GPT-5.4、GPT-5.4 mini、GPT-5 mini、Grok 4.5。Grok 4.5 在支援／價格頁仍列出的衝突另記快照，採日期明確的淘汰公告。
- **11 月 16 日預定淘汰**：Claude Opus 4.8、Claude Opus 5、GPT-5.6 Terra。Opus 4.8 對年繳個人方案有例外；公告未明指 fast mode，未擅自套用至 fast mode。
- Terra 5.6 在 10 月 15 日公告的替代建議為 Sol 6.1 或 Luna 6；10 月 26 日推出的 **Terra 6.1 為直接同產品線後繼者**。CSV 分欄保存兩種關係。
- 10 月 2 日淘汰的 Gemini 3.5／3.6 Flash、Kimi K2.7 Code、Opus 4.7 保留歷史列。Sonnet 4.6 僅年繳個人方案可用。
- 主圖排除被直接後繼者取代的舊款：Luna 5.6 → 6；Sol 5.6／6 → 6.1；Terra 5.6 → 6.1；Sonnet 4.6／5 → 5.5；Opus 4.8／5 → 5.5；Haiku 4.5 → 5.5；Fable 5 → 5.1；Grok 4.6 → 4.7。舊列與理由保留 CSV。
- AA 已加入 Kimi K3.1 Pro，但 GitHub 未列為支援，因此 Copilot 主圖仍保留 Kimi K3，不能套用新模型的分數。

## 資料缺口與查核限制

Gemini Flash/low 有 33 分，尚無 task cost。GPT-5.3-Codex/xhigh 搜尋仍為 33 分 estimate，但單模型頁超過擷取工具 4MiB 限制，當日 task cost 無法完整確認；原缺值紀錄保持排除，benchmark 查核日期保留 10 月 14 日。MAI-Code-1.1-Flash 未取得可比較的完整 AA 點。GPT-5.4 nano 僅 Codex VS Code extension／Pro+ 可用，排除一般 Copilot Chat 主圖。缺值不補零。

Kimi 單模型頁也超過擷取限制，改用**當日 AA 比較頁**核對 low 30／$1.15、max 44／$2.00；未採舊搜尋快取的 low 34 estimated。Argon 以當日搜尋摘要與 releases 清單交叉確認 53／$1.62，於 CSV 標明查核方式。

Luna、新 Terra non-reasoning 僅存 CSV；Copilot CLI effort 參數列 low／medium／high／xhigh／max，可用層級依模型與 client 而異。AA default fallback 是 benchmark harness 行為，不保證等同 Copilot 每個 request。Index 未完整呈現你的 repo 成功率與延遲。

## 驗證與重畫

`validation_2026-10-28.json` 記錄 CSV 唯一鍵、51 筆來源值、查核方式、官方價格、生命週期／促銷／後繼者、獨立雙 frontier 計算、同成本同分數等支配邊界案例。圖檔檢查含 PNG 解碼、SVG 結構、48 個標籤、線性軸、放大來源框、22 條同色 effort 細線、標籤無重疊／裁切；另實際目視 PNG 排版。

```powershell
python -m pip install -r .\copilot_pareto\requirements.txt
python .\copilot_pareto\plot_copilot_pareto.py --refresh --date 2026-10-28
python .\copilot_pareto\verify_copilot_pareto.py --date 2026-10-28
```

`--refresh` 合併同日期已查核 JSON，保留歷史資料，不連網或假設缺值。日期預設台灣當日，重畫須指定快照日期；腳本拒絕將舊 CSV 冒用新日期。本機可用套件路徑為 `C:\Users\ChrisTorng\AppData\Local\Temp\copilot-pareto-python`（PYTHONPATH），未更動全域 Python。

## 資料來源

- [GitHub 支援模型與生命週期](https://docs.github.com/en/copilot/reference/ai-models/supported-models)
- [GitHub AI credits、token 費率與促銷期限](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing)
- [Copilot CLI effort 參數](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference)
- [Terra 6.1 加入 Copilot](https://github.blog/changelog/2026-10-26-gpt-6-1-terra-in-github-copilot/)
- [10 月 19 日已生效淘汰公告](https://github.blog/changelog/2026-10-19-github-copilot-models-deprecated-on-october-19-2026/)
- [11 月 16 日預定淘汰與年繳例外](https://github.blog/changelog/2026-10-15-upcoming-deprecation-of-selected-github-copilot-models-in-mid-november/)
- [10 月 2 日淘汰公告](https://github.blog/changelog/2026-10-02-selected-models-in-github-copilot-deprecated/)
- [Sol 5.6 provider 促銷](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
- [AA 完整 Intelligence Index v4.3.2 與成本定義](https://artificialanalysis.ai/evaluations/artificial-analysis-intelligence-index)
- [AA 模型與 effort 清單](https://artificialanalysis.ai/models/releases)
- [AA Terra 6.1 分析](https://artificialanalysis.ai/articles/gpt-6-1-terra-pushes-the-cost-efficiency-frontier)
- [AA Haiku 暫定成本說明](https://artificialanalysis.ai/articles/claude-haiku-5-5)
- [AA Kimi low／max 比較頁](https://artificialanalysis.ai/models/comparisons/kimi-k3-low-vs-kimi-k3)
- [AA Argon/high](https://artificialanalysis.ai/models/gemini-4-argon)
- 其他逐點網址詳見 CSV 的 `benchmark_source`／`audit_source` 及來源 JSON。

## 2026-11-18 — AA Coding Agent Index v2.1（獨立參考版本）

新資料、雙平台 AA API 參考圖、Copilot／Kiro 計費資料層及缺值紀錄放在 `v21/`，入口為 `python copilot_pareto/run_coding_v21.py`。此入口沿用原 `plot_copilot_pareto.py`；舊 v2.0、104 列舊 CSV 及歷史圖保持原狀。正式每任務 Credits／平台成本 Pareto 因缺少可核實真實 Token／Credits，仍未建立；見 `v21/README.md`。
