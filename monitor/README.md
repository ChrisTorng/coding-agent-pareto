# Coding Agent Source Monitor

`source_registry.json` records **official first-stage sources** and **conditional second-stage source pages** needed by the ChatGPT automation `Coding Agent 模型／價格變更監測及 GHA 發布` (Tue–Sat 07:30 Asia/Taipei).

Each run: compare primary sources with reviewed/versioned benchmark and platform rate snapshots. Only when a material model availability/effort, USD-per-token or credit multiplier, promotion/expiry, or benchmark version/value change is detected, retrieve affected detailed model/comparison sources, cross-check the facts and update the corresponding historical snapshots. Preserve all providers including China and old historical rows; do not assign scores where none exist. If no real change: no commit, GitHub Actions run or notification. If changed: commit via the GitHub connector, verify GitHub Actions rendered the four original Python charts and interactive site, then verify the public site.

This file is a **source inventory**, not a claim that GitHub Actions itself refreshes price information automatically. Last reviewed rate snapshot remains the versioned CSV tracked in the repository. No external fetch results or hashes are fabricated in this manifest.
## Extended verification policy (2026-11-20)

The initial registry includes 16 required check-every-run sources, including the official Terminal-Bench v4.1 leaderboard and release news. The versioned leaderboard must be checked for newly added or revised scores and costs even when the benchmark version has not changed. For Copilot, Kiro and Claude Code, independently enumerate all model/effort names, rate tiers, promotions, deadlines and credit multipliers. ETags/hashes optimize unchanged network fetches, but cannot replace structured full-coverage comparisons. Missing or inaccessible rows are an incomplete audit, not no update.

Official Terminal-Bench v4.1 was released November 9, 2026 (https://www.tbench.ai/news/terminal-bench-4-1). The AA Coding Agent Index v2.1 includes TB 4.1 as a component; the existing static GitHub Fusion comparison remains an immutable historical 4.0 benchmark. Do not relabel old scores as 4.1. Adding an independently scored TB 4.1 Pareto comparison requires verifiable per-variant score and comparable per-task cost; rounded total benchmark costs cannot substitute for those exact cost values.

The model selector shows only models with at least one scored-and-costed point in the appropriate platform's existing charts. Maintain unscored Microsoft and all other models in the underlying source and pricing catalog for monitoring, without showing no-score entries in the selectable list.

## 2026-11-20 complete-source snapshots
The latest reviewed, source-attributed inventories now include official model availability for Copilot, Kiro, and current Claude Code aliases; 48 Copilot rate-tier rows, 19 Anthropic API-tier rows, and 15 documented Kiro credit multipliers. Public AA Intelligence Index v5.0.1 features 28 selected model variants (not all evaluated model/effort variants); TB 4.1 publishes 66 ranked submissions. The new TB v4.1 chart uses *official rounded full-submission costs in USD*, clearly differentiated from the historical v4.0 *USD per task* chart. Nothing is relabeled; all old static Matplotlib outputs remain unchanged.
