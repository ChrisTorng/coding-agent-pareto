# Coding Agent Pareto — Interactive Site

Static, dependency-free browser dashboard generated from versioned repository datasets using `python web/build_site.py`. The separate original Python/Matplotlib renderer is never replaced.

- Default: every provider and every model is selected; "Exclude China" deselects the China-based vendors in `web/build_site.py`.
- Provider and model checkboxes; search models; choose benchmark and historical snapshot.
- Two-panel interactive SVG chart (complete cost range and low-cost zoom), focus/hover tooltips, Pareto frontier, effort variants, downloadable filtered CSV.
- Data gaps remain visible as unscored models in the model catalog; an unscored model is never plotted at an invented score.
- Four original approved Python charts are copied verbatim to `dist/site/charts/*.png` and `*.svg`.
- GHA upload provides reproducible site asset ZIP plus PNG/SVG/CSV, and publishes to GitHub Pages.
- Intended custom domain: `coding-agent-pareto.christorng.idv.tw`. GitHub Pages must be configured with this domain in **Settings → Pages**. DNS requires a CNAME to `christorng.github.io`.

Published site is public; repository is public. Current source/frozen results are from dated versions; live data updates are intentionally not fabricated.

Local: `python copilot_pareto/run_four_charts_2026-11-18.py && python web/build_site.py && python scripts/check_site.py`.