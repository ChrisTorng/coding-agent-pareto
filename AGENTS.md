# Repository working rules

- Use existing `copilot_pareto/plot_copilot_pareto.py` and historical CSVs; do not replace or reimplement the renderer.
- Figures: white background; all-English; two panels with full cost and low-cost zoom; linear X-axis; effort labels, Pareto frontier and original label collision avoidance.
- Chart 1 retains existing labels; charts 2–4 label low-cost models on the left panel too.
- Never use image-generation AI for these plots. Use Python / Matplotlib.
- Keep AA v2.0, AA v2.1, DeepSWE 1.1, and Terminal-Bench 4.0 separate. Retain missing values as unknown, do not fabricate them.
- Maintain reproducible pinned data and update source citations when a new benchmark version is deliberately introduced.
- Generated PNG/SVG/CSV are delivered via GitHub Actions Artifact. Historical snapshots remain version-controlled.
