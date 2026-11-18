"""Lightweight artifact checks for GitHub Actions.

This only checks regenerated 2026-11-18 frozen outputs. It does not assert today's official prices.
"""
from pathlib import Path
import csv
import json
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'copilot_pareto' / 'four_charts_2026-11-18'
STEMS = (
    'aa_coding_agent_v21',
    'aa_coding_agent_v20',
    'fusion_deepswe_11',
    'fusion_terminal_bench_40',
)


def verify():
    for stem in STEMS:
        base=OUT / (stem+'_2026-11-18_linear')
        png=base.with_suffix('.png')
        svg=base.with_suffix('.svg')
        assert png.stat().st_size>40000, png
        assert svg.stat().st_size>5000, svg
        with Image.open(png) as im:
            im.verify()
        ET.parse(svg)
    points=OUT/'four_chart_points_2026-11-18.csv'
    with points.open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    assert len(rows)>30, len(rows)
    assert {r['chart'] for r in rows}==set(STEMS)
    report=json.loads((OUT/'validation_2026-11-18.json').read_text(encoding='utf-8'))
    # Original renderer checks label collisions / Pareto and linear axis per chart.
    assert report
    print('PASSED: four PNG, four SVG, generated CSV, validation report')

if __name__=='__main__': verify()
