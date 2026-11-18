# Copilot / Kiro Pareto Monitor

This repository contains the **existing** `copilot_pareto` Python/Matplotlib rendering engine, source data snapshots, historical CSVs and benchmark comparisons. It is not a reimplementation.

## Generate four charts with GitHub Actions

Open **Actions > Render Pareto Charts > Run workflow**. Each successful run publishes a downloadable **`copilot-pareto-charts-<run number>`** Artifact containing four PNG charts, four SVG charts, generated CSV and the renderer's validation report. Artifacts are not committed to Git; GitHub's Artifact retention policy applies (currently configured to 90 days).

You can also run locally:

```bash
python -m pip install -r copilot_pareto/requirements.txt
python copilot_pareto/run_four_charts_2026-11-18.py
python scripts/verify_ci_outputs.py
```

The four figures preserve the approved **2026-10-28 white-background, English-only, two-panel, linear-X-axis** visualization, with full-range left view and low-cost right zoom. Chart 1 preserves its original label policy; charts 2-4 label low-cost models in the left panel. The original Python plotter is at `copilot_pareto/plot_copilot_pareto.py`.

| Chart | Source | Notes |
|---|---|---|
| AA Coding Agent Index v2.1 | Pinned `copilot_pareto/v21/coding_agent_data_2026-11-18.csv` | Cross-harness reference, not Copilot native billing |
| AA Coding Agent Index v2.0 | Pinned `copilot_pareto/v2/coding_agent_data_2026-10-30.csv` | Fusion Max benchmark discount scenario |
| Fusion vs Fixed Models — DeepSWE 1.1 | `copilot_pareto/four_charts_2026-11-18/benchmark_snapshot_and_discount_sensitivity.csv` | Three Fusion efforts, 30% promo scenario |
| Fusion vs Fixed Models — Terminal-Bench 4.0 | Same benchmark snapshot | Three Fusion efforts, 30% promo scenario |

### Data and history

- `copilot_pareto/copilot_pareto_data.csv`: original historical model and effort CSV, 104 records.
- `copilot_pareto/source_snapshot_*.json`: archived official price/catalog snapshots.
- `copilot_pareto/v2/`, `copilot_pareto/v21/`: separate AA benchmark versions, raw CSV and JSON, provenance and validation.
- `copilot_pareto/monitor/`: comparison baselines.
- `copilot_pareto/four_charts_2026-11-18/`: frozen benchmark snapshot and generated point CSV.

**The current workflow is deliberately reproducible from pinned 2026 datasets.** It does not fetch or fabricate new AA benchmark values or platform Credits. Future automated model monitoring and data refresh will be designed separately after this CI has been verified. Price promotions are annotated as archived snapshot terms, not assumed to extend beyond their dates.

Historical approved PNG/SVG files remain in the Library backup bundle; only code and source datasets are versioned here. CI generates new chart assets for each run. Previous artifacts may expire, so retain key approved images in Git or a Release for long-term preservation if needed.
