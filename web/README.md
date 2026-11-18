# Coding Agent Pareto — interactive model explorer

Live: https://coding-agent-pareto.christorng.idv.tw/  
Source: https://github.com/ChrisTorng/coding-agent-pareto

## Interface

- First choose **GitHub Copilot**, **Kiro**, or **Claude Code**. Each platform has a separately verified model catalog and benchmark snapshots. Platforms do not share pricing.
- Select companies and child models; a partially selected company has an indeterminate checkbox. **All models selected** is the default. **Exclude China** filters by company country, not model name.
- Select any benchmark or historical snapshot available for the platform. A missing score remains a catalog entry, never an invented plotted point.
- Large single interactive SVG graph: X minimum/maximum selectors below the axis, Y minimum/maximum selectors beside the axis, numeric fields, Pareto frontier, SVG hover/focus details, score/price clipping, reset axes.
- Fullscreen keeps benchmark selector, platform selector, axis controls and exports available. Export the current view as **PNG/SVG/CSV** or download the **original approved two-panel PNG/SVG** on the four Copilot benchmarks.
- Official promotional rates/expiration are surfaced for Copilot, model-level Kiro credit multipliers for Kiro, and official Claude API pricing for Claude Code where available. Benchmark task costs remain benchmark estimates, not transformed into made-up cross-platform prices.
- Light/dark mode styles align the chart with the surrounding page, including Dark Reader detection.

## Sources and matching

- GitHub Copilot supported models: https://docs.github.com/en/copilot/reference/ai-models/supported-models
- GitHub Copilot prices and promotions: https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing
- Copilot Fusion: https://docs.github.com/en/copilot/concepts/models/copilot-fusion
- Kiro models: https://kiro.dev/docs/models/available-models/
- Kiro billing: https://kiro.dev/pricing/
- Claude Code available model aliases: https://code.claude.com/docs/en/model-config
- Claude API pricing: https://platform.claude.com/docs/en/about-claude/pricing

Model availability is explicitly limited to the declared platform. Archived model versions remain cataloged when the underlying benchmark is historical. Some current model releases lack an AA score and consequently appear only in the catalog. The build uses pinned inputs: there is no invented live score or dynamic price scraping.

## Build and deployment

`python copilot_pareto/run_four_charts_2026-11-18.py && python web/build_site.py && python scripts/check_site.py`

Optional local browser smoke test: `python scripts/browser_smoke.py` (requires Playwright and Chromium).

`publish-site.yml` produces all four preserved Python/Matplotlib static white, English, two-panel charts plus the interactive site, and publishes `web/data.json` and `web/charts/` in this public repository. Every successful run also uploads a GitHub Actions Artifact. GitHub Pages is optional until enabled in Settings; the live custom hostname is currently hosted via Cloudflare Worker `deploy/cloudflare-proxy-worker.js`, proxying the generated public GitHub assets.