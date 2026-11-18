# Repository working rules

- Use existing `copilot_pareto/plot_copilot_pareto.py` and historical CSVs; do not replace or reimplement the renderer.
- Figures: white background; all-English; two panels with full cost and low-cost zoom; linear X-axis; effort labels, Pareto frontier and original label collision avoidance.
- Chart 1 retains existing labels; charts 2–4 label low-cost models on the left panel too.
- Never use image-generation AI for these plots. Use Python / Matplotlib.
- Keep AA v2.0, AA v2.1, DeepSWE 1.1, and Terminal-Bench 4.0 separate. Retain missing values as unknown, do not fabricate them.
- Maintain reproducible pinned data and update source citations when a new benchmark version is deliberately introduced.
- Generated PNG/SVG/CSV are delivered via GitHub Actions Artifact. Historical snapshots remain version-controlled.

## Interactive site invariants

- The interactive site is **one large SVG plot**, not the static two-panel Matplotlib composition. Include an adjustable X cost range below the axis and adjustable Y score range beside it, numeric bounds, score/cost clipping, Pareto frontier, fullscreen with platform / benchmark / range controls, and current-view PNG/SVG/CSV exports.
- Keep **GitHub Copilot / Kiro / Claude Code** as explicit platform choices. Match only each platform's verified model availability and independently priced or credited data. Do not reuse Copilot costs as Kiro charges or claim a model is available on a platform without a source. Keep unavailable scores unplotted.
- Show company → child-model hierarchical checkboxes; parents use indeterminate state when partially selected. Start with all models selected; one-click Exclude China is based on provider country. Display every provider's country.
- Keep the historical benchmark selector, all non-China models, China models for optional inspection, and all measured Fusion Standard/High/Max benchmark variants visible under the appropriate benchmark. If Fusion is unmeasured on AA v2.1, offer a direct path to its measured DeepSWE and Terminal-Bench records rather than invent a score.
- Support light/dark/Dark Reader readability and responsive/mobile use. Use only the existing supported libraries; no image-generation model for benchmark figures.
- Generate the site via `web/build_site.py`; run `scripts/check_site.py` and the browser smoke test after changes. Keep the accepted four static Python graphs exactly as before, and verify the new GitHub Actions artifact and public site before claiming completion.
- Repository visibility defaults to public unless the user explicitly asks for private.
