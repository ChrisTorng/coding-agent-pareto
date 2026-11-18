"""Refresh an audited snapshot and plot the Copilot cost/intelligence frontier.

All costs are AA workload proxies. Provisional costs have a separate frontier.
Run: python plot_copilot_pareto.py --refresh --date 2026-10-28
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.transforms import Bbox

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "copilot_pareto_data.csv"
INDEX_FIELD = "intelligence_index_v4_3_2"
COLORS = {"OpenAI": "#00866a", "Anthropic": "#cf6d42", "Google": "#3979db",
          "xAI": "#596473", "Moonshot AI": "#7c59ba", "Microsoft": "#0078d4"}
EFFORT_ORDER = {effort: i for i, effort in enumerate(["low", "medium", "high", "xhigh", "max"])}
SUCCESSORS = {
    "GPT-5.6 Luna": "GPT-6 Luna", "GPT-5.6 Sol": "GPT-6.1 Sol",
    "GPT-6 Sol": "GPT-6.1 Sol", "Claude Sonnet 5": "Claude Sonnet 5.5",
    "Claude Sonnet 4.6": "Claude Sonnet 5.5", "Claude Opus 5": "Claude Opus 5.5",
    "Claude Opus 4.8": "Claude Opus 5.5", "Claude Haiku 4.5": "Claude Haiku 5.5",
    "Claude Fable 5": "Claude Fable 5.1", "Grok 4.6": "Grok 4.7",
}


@dataclass(frozen=True)
class Point:
    provider: str
    model: str
    effort: str
    score: float
    cost: float
    score_status: str
    cost_status: str
    fallback: bool

    @property
    def label(self) -> str:
        return f"{self.model}/{self.effort}"


def read_rows() -> list[dict[str, str]]:
    with DATA_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def refresh_csv(snapshot_path: Path) -> None:
    source = json.loads(snapshot_path.read_text(encoding="utf-8-sig"))
    date = source["snapshot_date"]
    assert source["index_version"] == "4.3.2", "Update index schema before changing versions"
    rows = read_rows()
    fields = list(rows[0]) + ["snapshot_date", "benchmark_checked_at", "pricing_checked_at",
                            "availability_status", "retirement_date", "successor", "cost_note"]
    fields = list(dict.fromkeys(fields))
    by_key = {(row["model"], row["effort"]): row for row in rows}
    catalog = {entry["model"]: entry for entry in source["catalog"]}
    prices = {entry["model"]: entry for entry in source["prices"] if entry["tier"] == "default"}
    successors = {**SUCCESSORS, **source.get("direct_successors", {})}
    audited_keys = {(r["model"], r["effort"]) for r in source["records"]}
    fields = list(dict.fromkeys(fields + ["suggested_alternative", "audit_method", "audit_source"]))

    def new_row(model: str, effort: str, provider: str) -> dict[str, str]:
        row = {field: "" for field in fields}
        row.update(provider=provider, model=model, effort=effort, score_status="not_refreshed",
                   cost_status="not_refreshed", fallback="no", included_main="no",
                   exclusion_reason="Lifecycle record only; no benchmark values imported",
                   pricing_source=source["github_pricing_source"])
        rows.append(row)
        by_key[(model, effort)] = row
        return row

    for row in rows:
        row["snapshot_date"] = date
        row.setdefault("benchmark_checked_at", "2026-09-30")
        row.setdefault("cost_note", "Historical benchmark value retained; not re-fetched in this run")
        if (row["model"], row["effort"]) not in audited_keys:
            row["cost_note"] = "Historical benchmark value retained; not re-fetched in this run"
        # Only freshly audited records may remain on the current main chart.
        if row["included_main"] == "yes":
            row.update(included_main="no", exclusion_reason="No current audited benchmark record")
    for record in source["records"]:
        assert record["version"] == "4.3.2", record
        model, effort = record["model"], record["effort"]
        row = by_key.get((model, effort)) or new_row(model, effort, catalog[model]["provider"])
        row.update({INDEX_FIELD: "" if record["score"] is None else str(record["score"]),
                    "aa_cost_usd_task": "" if record["cost"] is None else str(record["cost"]),
                    "score_status": record["score_status"], "cost_status": record["cost_status"],
                    "fallback": "yes" if record["fallback"] else "no",
                    "benchmark_source": record["url"], "benchmark_checked_at": date,
                    "audit_method": record.get("audit_method", "model_page"),
                    "audit_source": record.get("audit_url", record["url"]),
                    "cost_note": "AA weighted workload cost; default-tier proxy, not actual Copilot billing"})
        if record["cost_status"] == "provisional":
            row["cost_note"] = "Provisional: AA excludes Haiku >100K input tier (5x rates); separate provisional frontier"
        row["included_main"] = "yes" if record["score"] is not None and record["cost"] is not None else "no"
        row["exclusion_reason"] = "" if row["included_main"] == "yes" else "AA cost per Intelligence Index task unavailable"
        if record.get("include_main") is False:
            row.update(included_main="no", exclusion_reason=record["exclusion_reason"])
        if record["input"] is not None:
            assert math.isclose(record["input"], prices[model]["input"]), model
            assert math.isclose(record["output"], prices[model]["output"]), model
    for model, entry in catalog.items():
        if not any(row["model"] == model for row in rows):
            row = new_row(model, "default", entry["provider"])
            if model == "GPT-5.4 nano":
                row["exclusion_reason"] = "Only in Codex VS Code extension (Pro+); not available in Copilot Chat"
            elif "fast mode" in model:
                row["exclusion_reason"] = "Legacy Opus 4.8 fast mode; excluded from current representative generations"
    for entry in source["retired"]:
        model = entry["model"]
        row = by_key.get((model, "default")) or new_row(model, "default", entry["provider"])
        row.update(availability_status="retired", retirement_date=entry["date"], successor=entry["successor"],
                   exclusion_reason=f"Retired {entry['date']}; successor {entry['successor']}")
    for row in rows:
        model = row["model"]
        row["snapshot_date"] = date
        row["pricing_checked_at"] = date if model in prices else ""
        row["pricing_source"] = source["github_pricing_source"]
        if model in catalog:
            row["availability_status"] = "supported"
        if model in source["scheduled_retirements"]:
            deadline = source["scheduled_retirements"][model]
            status = "retired" if date >= deadline else "retirement_scheduled"
            row.update(availability_status=status, retirement_date=deadline,
                       suggested_alternative=source.get("scheduled_alternatives", {}).get(model, ""),
                       successor=source.get("scheduled_alternatives", {}).get(model, row["successor"]),
                       included_main="no", exclusion_reason=f"Retirement {deadline}; newer generation available")
        if model in successors:
            row.update(successor=successors[model], included_main="no",
                       exclusion_reason=f"Direct successor {successors[model]}; retain old generation for traceability")
        if model in prices:
            price = prices[model]
            for field, key in [("copilot_input_per_m", "input"), ("copilot_cached_input_per_m", "cached_input"),
                               ("copilot_cache_write_per_m", "cache_write"), ("copilot_output_per_m", "output")]:
                row[field] = "" if price[key] is None else str(price[key])
            row["copilot_pricing_status"] = "GA default tier " + price["threshold"]
        else:
            row["copilot_pricing_status"] = "Historical price; absent from current GitHub pricing table"
        for promotion in source.get("promotions", []):
            if model == promotion["model"]:
                description = "Copilot promotional pricing" if promotion["scope"] == "copilot" else "GA; provider promotion (not a Copilot expiry commitment)"
                row.update(promotion_deadline=promotion["deadline"], copilot_pricing_status=description)
        exceptions = source.get("annual_plan_exceptions", {"Claude Sonnet 4.6": "2026-09-01"})
        if model in exceptions and date >= exceptions[model]:
            row.update(availability_status="annual_individual_plans_only", retirement_date=exceptions[model])
        if model == "MAI-Code-1.1-Flash":
            row.update(cost_note="No comparable AA point verified; excluded, not treated as zero", benchmark_checked_at=date)
    validate_rows(rows, date)
    with DATA_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validate_rows(rows: list[dict[str, str]], date: str) -> None:
    keys = [(row["model"], row["effort"]) for row in rows]
    assert len(keys) == len(set(keys)), "Duplicate model/effort"
    for row in rows:
        assert row["model"].lower() != "auto"
        assert row["snapshot_date"] == date, row
        assert row["included_main"] in {"yes", "no"}
        if row["included_main"] == "no":
            assert row["exclusion_reason"], row
            continue
        assert row["availability_status"] == "supported", row
        assert row["effort"] in EFFORT_ORDER, row
        assert row["model"] not in SUCCESSORS, row
        assert not row["successor"], row
        assert row["benchmark_checked_at"] == date and row["pricing_checked_at"] == date, row
        assert row["cost_status"] in {"published", "provisional"}, row
        assert row["score_status"] in {"measured", "estimated"}, row
        for key in [INDEX_FIELD, "aa_cost_usd_task"]:
            value = float(row[key])
            assert math.isfinite(value) and value >= 0, row


def load_points() -> list[Point]:
    return [Point(row["provider"], row["model"], row["effort"], float(row[INDEX_FIELD]),
                  float(row["aa_cost_usd_task"]), row["score_status"], row["cost_status"], row["fallback"] == "yes")
            for row in read_rows() if row["included_main"] == "yes"]


def pareto_frontier(points: list[Point]) -> list[Point]:
    return sorted([p for p in points if not any(
        q.cost <= p.cost and q.score >= p.score and (q.cost < p.cost or q.score > p.score)
        for q in points)], key=lambda p: (p.cost, p.score, p.label))


def label_points(ax, points: list[Point], all_points: list[Point], frontier: list[Point]) -> list:
    """Choose deterministic display-coordinate anchors without overlapping labels."""
    renderer = ax.figure.canvas.get_renderer()
    placed, annotations = [], []
    area = ax.get_window_extent()
    point_xy = [ax.transData.transform((p.cost, p.score)) for p in all_points]
    line_xy = [ax.transData.transform((p.cost, p.score)) for p in frontier]
    samples = []
    for start, end in zip(line_xy, line_xy[1:]):
        count = max(2, int(math.dist(start, end) / 6))
        samples.extend([(start[0]+(end[0]-start[0])*k/count, start[1]+(end[1]-start[1])*k/count) for k in range(count+1)])
    frontier_labels = {p.label for p in frontier}
    for point in sorted(points, key=lambda p: (p.cost, -p.score)):
        origin = ax.transData.transform((point.cost, point.score))
        weight = "bold" if point.label in frontier_labels else "normal"
        font = matplotlib.font_manager.FontProperties(family="DejaVu Sans", size=9.5, weight=weight)
        width, height, _ = renderer.get_text_width_height_descent(point.label, font, ismath=False)
        width += 9
        height += 10
        best = None
        for radius in [18, 35, 55, 80, 110, 145, 185, 225]:
            for angle in [30, -30, 70, -70, 110, -110, 150, -150, 0, 180]:
                dx, dy = radius*math.cos(math.radians(angle)), radius*math.sin(math.radians(angle))
                cx, cy = origin[0]+dx, origin[1]+dy
                left = cx if dx >= 0 else cx-width
                box = Bbox.from_bounds(left, cy-height/2, width, height)
                outside = max(0, area.x0-box.x0)+max(0, box.x1-area.x1)+max(0, area.y0-box.y0)+max(0, box.y1-area.y1)
                overlap = sum(max(0, min(box.x1,b.x1)-max(box.x0,b.x0))*max(0,min(box.y1,b.y1)-max(box.y0,b.y0)) for b in placed)
                collisions = sum(box.padded(4).contains(*xy) for xy in point_xy)
                on_line = sum(box.padded(2).contains(*xy) for xy in samples)
                penalty = outside*1e7 + overlap*1e5 + collisions*1e5 + on_line*3000 + radius
                candidate = (penalty, left+4, cy, box)
                if best is None or penalty < best[0]:
                    best = candidate
        _, left, cy, box = best
        anchor = ax.transData.inverted().transform((left, cy))
        annotation = ax.annotate(point.label, (point.cost, point.score), xytext=anchor,
            fontsize=9.5, fontweight=weight, ha="left", va="center",
            color="#16202a" if weight == "bold" else COLORS[point.provider],
            arrowprops={"arrowstyle":"-", "color":"#a5adb7", "lw":0.65},
            bbox={"facecolor":"#fbfcfe", "edgecolor":"none", "pad":1.4, "alpha":0.94}, zorder=6)
        placed.append(box.padded(2))
        annotations.append(annotation)
    return annotations


def plot(points: list[Point], date: str, config: dict | None = None) -> dict:
    config = config or {}
    frontier = pareto_frontier([p for p in points if p.cost_status == "published"])
    provisional_frontier = pareto_frontier(points)
    plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":11, "svg.fonttype":"none"})
    fig, axes = plt.subplots(1, 2, figsize=(23, 11.4), dpi=180, gridspec_kw={"width_ratios":[1.22, 1]})
    fig.patch.set_facecolor("#fbfcfe")
    fig.subplots_adjust(left=0.043, right=0.983, top=0.855, bottom=0.17, wspace=0.11)
    max_cost = max(p.cost for p in points)
    model_lines = []
    for panel, ax in enumerate(axes):
        ax.set_facecolor("#fbfcfe")
        ax.set_xscale("linear")
        ax.set_ylim(*config.get('ylim', (20, 60)))
        ax.set_yticks(range(math.ceil(config.get('ylim',(20, 60))[0] / 5)*5, config.get('ytop', 60)+1, 5))
        ax.grid(color="#dce2e9", lw=0.65)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xlabel(config.get('xlabel', "AA cost per Intelligence Index task (USD; linear)"), labelpad=12)
        for model_index, model in enumerate(sorted({p.model for p in points})):
            group = sorted([p for p in points if p.model == model], key=lambda p: EFFORT_ORDER[p.effort])
            if len(group) < 2:
                continue
            color = COLORS[group[0].provider]
            gid = f"model-effort-{panel}-{model_index}"
            line, = ax.plot([p.cost for p in group], [p.score for p in group],
                            color=color, lw=0.9, alpha=0.6, zorder=2)
            line.set_gid(gid)
            model_lines.append({"panel": panel, "model": model, "efforts": [p.effort for p in group],
                                "color": color, "linewidth": 0.9, "svg_id": gid})
        for provider, color in COLORS.items():
            for status, marker in [("published","o"),("provisional","D")]:
                group = [p for p in points if p.provider==provider and p.cost_status==status]
                if group:
                    ax.scatter([p.cost for p in group], [p.score for p in group], s=57, marker=marker,
                               c=color, edgecolors="white", linewidths=0.8, zorder=4)
        ax.plot([p.cost for p in frontier], [p.score for p in frontier], c="#14202c", lw=2.7, zorder=3)
        ax.scatter([p.cost for p in frontier], [p.score for p in frontier], s=128, facecolors="none",
                   edgecolors="#14202c", linewidths=1.7, zorder=5)
        for start, end in zip(provisional_frontier, provisional_frontier[1:]):
            if start.cost_status == "provisional" or end.cost_status == "provisional":
                ax.plot([start.cost,end.cost],[start.score,end.score], c=COLORS["Anthropic"], lw=2.2, ls="--", zorder=3)
        provisional = [p for p in provisional_frontier if p.cost_status=="provisional"]
        if provisional:
            ax.scatter([p.cost for p in provisional],[p.score for p in provisional], s=125, marker="D",
                       facecolors="none",edgecolors=COLORS["Anthropic"],lw=1.8,zorder=5)
    axes[0].set_xlim(-0.07, max(8, max_cost*1.055))
    axes[0].set_xticks(range(0, math.ceil(max(8, max_cost*1.055))+1, 2))
    axes[0].set_title("Full cost range: boxed area shown at right", loc="left", pad=18, fontsize=14, fontweight="bold")
    axes[0].set_ylabel(config.get('ylabel', "Artificial Analysis Intelligence Index v4.3.2"), labelpad=10)
    axes[1].set_xlim(*config.get('zoom', (-0.012, 0.85)))
    if not config:
        axes[1].set_xticks([i/10 for i in range(9)])
    axes[1].set_title("Low-cost detail: same data, linear axis", loc="left", pad=18, fontsize=14, fontweight="bold")
    zoom_x, zoom_y = axes[1].get_xlim(), axes[1].get_ylim()
    zoom_box = Rectangle((zoom_x[0], zoom_y[0]), zoom_x[1]-zoom_x[0], zoom_y[1]-zoom_y[0],
                         facecolor=(0.22, 0.47, 0.86, 0.035), edgecolor="#3979db",
                         linewidth=1.5, linestyle=(0, (5, 3)), zorder=2.5, clip_on=False)
    zoom_box.set_gid("zoom-source-range")
    axes[0].add_patch(zoom_box)
    fig.text(0.043,0.96,config.get('title', "GitHub Copilot model / effort Pareto frontier"),fontsize=22,fontweight="bold")
    fig.text(0.043,0.921,config.get('subtitle', f"Snapshot {date} (Asia/Taipei)  |  Current representative models  |  No Auto  |  Both cost axes are linear"),
             fontsize=12,color="#4d5966")
    fig.canvas.draw()
    split = config.get('split', 0.8)
    high = [p for p in points if p.cost > split]
    low = [p for p in points if p.cost <= split]
    # On the three sparse benchmark charts, label the low-cost points in the full-range left panel too.
    # Leave the dense AA v2.1 chart unchanged; right-hand zoom always retains its original labels.
    left_panel_points = points if config.get("label_low_on_full", False) else high
    annotations = [label_points(axes[0],left_panel_points,points,frontier), label_points(axes[1],low,low,frontier)]
    providers = [Line2D([0],[0],marker="o",color=c,ls="none",label=p,markersize=7) for p,c in COLORS.items() if any(x.provider==p for x in points)]
    provisional_points = [p for p in provisional_frontier if p.cost_status == "provisional"]
    styles = [Line2D([0],[0],color="#14202c",lw=2.5,marker="o",markerfacecolor="none",label=f"Pareto frontier ({len(frontier)} points)"),
              Line2D([0],[0],color=COLORS["Anthropic"],ls="--" if provisional_points else "none",marker="D",markerfacecolor="none",
                     label="Provisional-cost frontier" if provisional_points else "Provisional costs (all dominated)")]
    if config:
        styles = [Line2D([0],[0],color="#14202c",lw=2.5,marker="o",markerfacecolor="none",label=config.get('frontier_legend', f"AA API reference frontier ({len(frontier)} points)"))]
    fig.legend(handles=providers+styles, loc="lower center",bbox_to_anchor=(0.5,0.086),ncol=7,frameon=False,fontsize=10.5)
    fig.text(0.043,0.060,config.get('note1', "Haiku 5.5 diamonds: provisional AA costs omit the >100K input tier (5x rates); they do not dominate the solid frontier."),fontsize=10.5,color="#7d462d")
    fig.text(0.043,0.033,config.get('note2', "AA benchmark workload proxy, not your Copilot bill.  1 AI credit = US$0.01.  Sources and fallback details: README / CSV."),fontsize=10.5,color="#596574")
    source = {} if config else json.loads((ROOT / f"source_snapshot_{date}.json").read_text(encoding="utf-8"))
    promotions = [p["model"] + ": " + p["deadline"] for p in source.get("promotions", []) if p["scope"] == "copilot"]
    fig.text(0.043,0.010,config.get('footer', "Copilot promotional price deadlines: " + "; ".join(promotions)),fontsize=10,color="#596574")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    overlaps, clipped = [], []
    for panel, texts in enumerate(annotations):
        boxes = [(a.get_text(),a.get_bbox_patch().get_window_extent(renderer)) for a in texts]
        area = axes[panel].get_window_extent()
        for i,(label,box) in enumerate(boxes):
            if not (area.contains(box.x0,box.y0) and area.contains(box.x1,box.y1)):
                clipped.append(label)
            for other,other_box in boxes[i+1:]:
                if box.overlaps(other_box):
                    overlaps.append([label,other])
    assert not overlaps, f"Overlapping labels: {overlaps}"
    assert not clipped, f"Clipped labels: {clipped}"
    stem = Path(config['stem']) if config else ROOT / f"copilot_model_pareto_{date}_linear"
    fig.savefig(stem.with_suffix(".png"), facecolor=fig.get_facecolor())
    fig.savefig(stem.with_suffix(".svg"), facecolor=fig.get_facecolor(), metadata={"Date":date})
    report = {"snapshot_date":date, "index_version":config.get('version', '4.3.2'), "rows":len(read_rows()), "plotted_points":len(points),
              "published_cost_points":len(points)-sum(p.cost_status=="provisional" for p in points),
              "provisional_cost_points":sum(p.cost_status=="provisional" for p in points),
              "linear_axes":all(ax.get_xscale()=="linear" for ax in axes),
              "zoom_source_bounds":{"x":list(zoom_x),"y":list(zoom_y)},
              "model_effort_lines":model_lines,
              "label_count":sum(map(len,annotations)), "label_overlaps":overlaps, "clipped_labels":clipped,
              "provisional_frontier_additions":len(provisional_points),
              "copilot_promotion_deadlines":promotions,
              "frontier":[{"model":p.model,"effort":p.effort,"score":p.score,"cost":p.cost} for p in frontier],
              "provisional_frontier":[{"model":p.model,"effort":p.effort,"score":p.score,"cost":p.cost} for p in provisional_frontier]}
    plt.close(fig)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=datetime.now(timezone(timedelta(hours=8))).date().isoformat(), help="Date of the audited data snapshot (default: today in Taipei)")
    parser.add_argument("--refresh", action="store_true", help="Merge audited JSON into CSV before plotting")
    args = parser.parse_args()
    if args.refresh:
        refresh_csv(ROOT / f"source_snapshot_{args.date}.json")
    rows = read_rows()
    assert all(row["snapshot_date"]==args.date for row in rows), "Requested date does not match audited CSV"
    validate_rows(rows,args.date)
    report = plot(load_points(),args.date)
    output = ROOT / f"validation_{args.date}.json"
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
