# Label-only update — 2026-11-18

- Original approved white-background, English, two-panel Matplotlib design preserved.
- Chart 1 (AA v2.1) is byte-for-byte unchanged.
- Charts 2–4 now label **all data points on the full-range left panel**, including low-cost points. The right panel is unchanged.
- No model data, cost, discounts, promotion notes, axes, or Pareto math changed.
- Added `label_low_on_full` in `plot_copilot_pareto.py` and selected it only for charts 2–4 in `run_four_charts_2026-11-18.py`.
- Every chart passed overlap, clipping, and linear-axis validation. Detailed proof in `label_update_2026-11-18.json`.

Run from the project root:

```
python copilot_pareto/run_four_charts_2026-11-18.py
```
