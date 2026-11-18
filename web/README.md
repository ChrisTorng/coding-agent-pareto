# Coding Agent Pareto — Interactive Site

Static, dependency-free browser dashboard generated from versioned repository datasets using `python web/build_site.py`. The separate original Python/Matplotlib renderer is never replaced.

- Default: every provider and every model is selected; "Exclude China" deselects the China-based vendors in `web/build_site.py`.
- Provider and model checkboxes; search models; choose benchmark and historical snapshot.
- Two-panel interactive SVG chart (complete cost range and low-cost zoom), focus/hover tooltips, Pareto frontier, effort variants, downloadable filtered CSV.
- Data gaps remain visible as unscored models in the model catalog; an unscored model is never plotted at an invented score.
- Four original approved Python charts are copied verbatim to `dist/site/charts/*.png` and `*.svg`.
- GHA upload provides reproducible website and chart assets; GitHub Pages deployment is prepared but skipped until Pages is enabled in repository Settings.
- **Live**: https://coding-agent-pareto.christorng.idv.tw/ — Cloudflare Worker currently serves the versioned public `web/` files from GitHub, including the latest GHA-generated `web/data.json` and `web/charts/` images. The Worker source is under `deploy/cloudflare-proxy-worker.js`.
- **GitHub Pages option**: after **Settings → Pages → Build and deployment → Source: GitHub Actions** is enabled once, the existing `publish-site.yml` deploy job runs automatically. To move the custom hostname to GitHub Pages directly, configure the Pages custom domain and change DNS to CNAME `christorng.github.io` (replacing the existing Worker Domain).

Published site is public; repository is public. Current source/frozen results are from dated versions; live data updates are intentionally not fabricated.

Local: `python copilot_pareto/run_four_charts_2026-11-18.py && python web/build_site.py && python scripts/check_site.py`.