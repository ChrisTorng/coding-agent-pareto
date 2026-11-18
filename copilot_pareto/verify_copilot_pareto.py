"""Independently verify the CSV, dominance calculation, PNG and SVG."""
from __future__ import annotations
import argparse
import csv
import importlib.util
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parent


def verify(date: str) -> dict:
    with (ROOT / "copilot_pareto_data.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    source = json.loads((ROOT / f"source_snapshot_{date}.json").read_text(encoding="utf-8"))
    report_path = ROOT / f"validation_{date}.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    keys = {(r["model"], r["effort"]): r for r in rows}
    assert len(keys) == len(rows)
    assert all(r["snapshot_date"] == date and r["model"].lower() != "auto" for r in rows)
    assert {x["model"] for x in source["catalog"]} <= {r["model"] for r in rows}
    for record in source["records"]:
        row = keys[(record["model"], record["effort"])]
        score = float(row["intelligence_index_v4_3_2"]) if row["intelligence_index_v4_3_2"] else None
        cost = float(row["aa_cost_usd_task"]) if row["aa_cost_usd_task"] else None
        assert score == record["score"] and cost == record["cost"]
        assert row["benchmark_checked_at"] == date
        assert row["cost_status"] == record["cost_status"]
        assert row["audit_method"] == record.get("audit_method", "model_page")
        assert row["audit_source"] == record.get("audit_url", record["url"])
        if record.get("include_main") is False:
            assert row["included_main"] == "no" and row["exclusion_reason"] == record["exclusion_reason"]
    prices = {r["model"]: r for r in source["prices"] if r["tier"] == "default"}
    for row in rows:
        if row["model"] in prices:
            price = prices[row["model"]]
            for column, field in [("copilot_input_per_m", "input"), ("copilot_cached_input_per_m", "cached_input"),
                                  ("copilot_cache_write_per_m", "cache_write"), ("copilot_output_per_m", "output")]:
                assert (float(row[column]) if row[column] else None) == price[field]
            assert row["pricing_checked_at"] == date
        else:
            assert not row["pricing_checked_at"], "Historical price must not appear current"
    main = [r for r in rows if r["included_main"] == "yes"]
    audited = {(r["model"], r["effort"]) for r in source["records"]}
    assert all((r["model"], r["effort"]) in audited for r in main)
    for row in main:
        assert row["availability_status"] == "supported"
        assert row["benchmark_checked_at"] == date and row["pricing_checked_at"] == date
    for promotion in source["promotions"]:
        assert all(r["promotion_deadline"] == promotion["deadline"] for r in rows if r["model"] == promotion["model"])
    for model, deadline in source["scheduled_retirements"].items():
        expected_status = "retired" if date >= deadline else "retirement_scheduled"
        exception_date = source.get("annual_plan_exceptions", {}).get(model)
        if exception_date and date >= exception_date:
            expected_status = "annual_individual_plans_only"
        assert all(r["availability_status"] == expected_status and r["included_main"] == "no" for r in rows if r["model"] == model)
    for model, successor in source.get("direct_successors", {}).items():
        assert all(r["included_main"] == "no" and r["successor"] == successor and successor in r["exclusion_reason"]
                   for r in rows if r["model"] == model)
    for record in source.get("unverified_records", []):
        row = keys[(record["model"], record["effort"])]
        assert row["included_main"] == "no" and row["benchmark_checked_at"] < date
    eligible = [r for r in main if r["cost_status"] == "published"]
    # Independent ascending-cost scan; keep all exact duplicates at a cost/score.
    groups = {}
    for row in eligible:
        groups.setdefault(float(row["aa_cost_usd_task"]), []).append(row)
    scan, best = set(), -math.inf
    for cost in sorted(groups):
        maximum = max(float(r["intelligence_index_v4_3_2"]) for r in groups[cost])
        if maximum > best:
            scan.update((r["model"], r["effort"]) for r in groups[cost]
                        if float(r["intelligence_index_v4_3_2"]) == maximum)
            best = maximum
    assert scan == {(p["model"], p["effort"]) for p in report["frontier"]}
    # Verify the provisional frontier separately so incomplete cost cannot silently
    # remove a comparable-cost point from the solid frontier.
    provisional_scan = {(r["model"], r["effort"]) for r in main if not any(
        float(q["aa_cost_usd_task"]) <= float(r["aa_cost_usd_task"])
        and float(q["intelligence_index_v4_3_2"]) >= float(r["intelligence_index_v4_3_2"])
        and (float(q["aa_cost_usd_task"]) < float(r["aa_cost_usd_task"])
             or float(q["intelligence_index_v4_3_2"]) > float(r["intelligence_index_v4_3_2"]))
        for q in main)}
    assert provisional_scan == {(p["model"], p["effort"]) for p in report["provisional_frontier"]}
    assert report["provisional_frontier_additions"] == sum(
        keys[key]["cost_status"] == "provisional" for key in provisional_scan)
    spec = importlib.util.spec_from_file_location("pareto_check", ROOT / "plot_copilot_pareto.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    P = module.Point
    edge_points = [P("OpenAI", name, "low", score, cost, "measured", "published", False)
                   for name, score, cost in [("same1", 2, 1), ("same2", 2, 1),
                                            ("worse", 1, 1), ("dearer", 2, 2), ("tradeoff", 3, 3)]]
    assert {p.model for p in module.pareto_frontier(edge_points)} == {"same1", "same2", "tradeoff"}
    png = ROOT / f"copilot_model_pareto_{date}_linear.png"
    with Image.open(png) as image:
        dimensions = image.size
        image.verify()
    svg = ET.parse(ROOT / f"copilot_model_pareto_{date}_linear.svg")
    assert svg.getroot().tag.endswith("svg")
    labels = [n.text for n in svg.iter() if n.tag.endswith("text") and n.text]
    expected = {r["model"] + "/" + r["effort"] for r in main}
    assert expected <= set(labels)
    assert sum(label in expected for label in labels) == len(main)
    elements = {node.attrib["id"]: node for node in svg.iter() if "id" in node.attrib}
    assert "zoom-source-range" in elements
    assert report["zoom_source_bounds"] == {"x": [-0.012, 0.85], "y": [20.0, 60.0]}
    model_groups = {}
    effort_order = {effort: i for i, effort in enumerate(["low", "medium", "high", "xhigh", "max"])}
    for row in main:
        model_groups.setdefault(row["model"], []).append(row)
    expected_lines = {(panel, model) for panel in range(2) for model, group in model_groups.items() if len(group) > 1}
    assert {(line["panel"], line["model"]) for line in report["model_effort_lines"]} == expected_lines
    for line in report["model_effort_lines"]:
        group = sorted(model_groups[line["model"]], key=lambda row: effort_order[row["effort"]])
        assert line["efforts"] == [row["effort"] for row in group]
        assert line["color"] == module.COLORS[group[0]["provider"]]
        paths = [node for node in elements[line["svg_id"]].iter() if node.tag.endswith("path")]
        assert len(paths) == 1 and f"stroke: {line['color']}" in paths[0].attrib["style"]
        assert "stroke-width: 0.9" in paths[0].attrib["style"]
    assert report["linear_axes"] and not report["label_overlaps"] and not report["clipped_labels"]
    report.update(csv_unique_keys=True, github_catalog_coverage=len(source["catalog"]),
                  source_records_matched=len(source["records"]), official_prices_matched=True,
                  independent_frontier_check=True, dominance_edge_cases=True,
                  independent_provisional_frontier_check=True, lifecycle_and_promotions_verified=True,
                  direct_successors_verified=True, audit_provenance_verified=True,
                  png_verified=True, png_dimensions=dimensions, svg_verified=True, svg_model_labels=len(main),
                  zoom_source_verified=True, model_effort_lines_verified=len(expected_lines))
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return {key: report[key] for key in ["rows", "plotted_points", "source_records_matched", "github_catalog_coverage",
            "official_prices_matched", "independent_frontier_check", "dominance_edge_cases", "linear_axes",
            "label_overlaps", "clipped_labels", "png_dimensions", "svg_model_labels",
            "zoom_source_verified", "model_effort_lines_verified"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    print(json.dumps(verify(parser.parse_args().date), indent=2))
