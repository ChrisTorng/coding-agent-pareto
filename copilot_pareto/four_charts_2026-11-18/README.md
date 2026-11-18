# Four Copilot Pareto charts — 2026-11-18

All four plots use the **original** `plot_copilot_pareto.py` / Matplotlib with the approved white/light English, two-panel, linear-X layout. Left = entire cost range; right = low-cost detail. Original point labels, label placement, model/effort connections, Pareto frontier and historical project files are preserved. No generative image model was used.

Run from the project root with `python copilot_pareto/run_four_charts_2026-11-18.py`. The runner reads the included CSVs and writes four PNG/SVG files, one unified points CSV and a JSON validation report to `copilot_pareto/four_charts_2026-11-18/`.

| Chart | Benchmark | Points | Fusion | X-axis treatment |
|---|---|---:|---|---|
| `aa_coding_agent_v21` | AA Coding Agent Index v2.1 | 25 | None measured in v2.1 | AA API task cost as supplied |
| `aa_coding_agent_v20` | AA Coding Agent Index v2.0 | 15 | Max | Fusion cost x 0.70 |
| `fusion_deepswe_11` | GitHub Benchmarks / DeepSWE 1.1 historical snapshot | 6 | Standard/High/Max | Fusion costs x 0.70 |
| `fusion_terminal_bench_40` | GitHub Benchmarks / Terminal-Bench 4.0 historical snapshot | 6 | Standard/High/Max | Fusion costs x 0.70 |

`four_chart_points_2026-11-18.csv` preserves the reported cost, applied factor, and plotted estimated cost **separately**. The two GitHub Benchmarks comparisons use historical numbers sourced from the November 2026 third-party summary; they have not been freshly independently reproduced.

## Promotions shown in all four plots

- Fusion: 30% off model costs through **2026-11-30**, applied to plotted Fusion points as scenario cost factor **0.70**.
- Auto model selection: 10% off on paid Copilot plans; Auto excluded from charts.
- Gemini 4 Argon / Carbon: 50% promotional token pricing until **2026-12-01**.
- Gemini 3.8 Flash: promotional token pricing through **2026-12-31**.
- MAI Code 2 / MAI Code 2 Flash: 50% promotional token pricing until **2027-05-17**.

Other model points retain the benchmark's reported estimated API cost. Without per-task token breakdown, these are not recalculated to GitHub's promotional token rates; in particular no extra Gemini / MAI discount is applied to an already benchmark-estimated API price. The figures are intended for model-selection reference, not an exact AI Credits bill. Promotion dates and percentages come from GitHub Docs and are current for 2026-11-18.

## Data provenance

- Artificial Analysis v2.0 source already archived under `copilot_pareto/v2/coding_agent_data_2026-10-30.csv`.
- Artificial Analysis v2.1 source already archived under `copilot_pareto/v21/coding_agent_data_2026-11-18.csv`.
- GitHub Benchmarks historical snapshot: `benchmark_snapshot_and_discount_sensitivity.csv` (from the prior user-approved comparison), secondary summary at https://zenn.dev/mochan_tk/articles/2caab47932dd9e .
- Official promotional pricing https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing and https://docs.github.com/en/copilot/concepts/models/copilot-fusion .

## Minimal edits to existing plotter

Only two backwards-compatible adjustments: y-axis ticks respect non-20 lower bounds for benchmarks with different score ranges, and the frontier legend can use a benchmark-appropriate label. Historical images and the historical CSV are unchanged.

All plots checked by the original function: both X axes linear; labels not clipped or overlapping; frontier independently calculated; all PNG/SVG outputs validated. See `validation_2026-11-18.json`.
