"""Render audited AA Coding Agent Index v2.1 reference plots through original plotter.

Data is manually transcribed from the AA v2.1 official comparisons on 2026-11-18.
The v2.0 legacy runner stays intact. No inferred platform task billing.
"""
from __future__ import annotations
import csv, json, hashlib
from pathlib import Path
from PIL import Image
import plot_copilot_pareto as original

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'v21'
DATE='2026-11-18'

def run():
    with (DATA/f'coding_agent_data_{DATE}.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==60
    assert all(r['version']=='2.1' and r['platform_task_credits']=='' and r['formal_frontier_eligible']=='False' for r in rows)
    assert len(set((r['platform'],r['model'],r['effort']) for r in rows))==len(rows)
    assert all((not r['reference_included']=='True') or (r['api_cost_usd_task'] and r['score']) for r in rows)
    report={}
    for platform in ['Copilot','Kiro']:
        selected=[r for r in rows if r['platform']==platform and r['reference_included']=='True']
        points=[original.Point(r['provider'],r['model'],r['effort'],float(r['score']),float(r['api_cost_usd_task']),'published','published',r['fallback']=='True') for r in selected]
        assert len(points)==(25 if platform=='Copilot' else 5)
        scan=[];best=-1
        for p in sorted(points,key=lambda p:(p.cost,-p.score)):
            if p.score>best:scan.append(p);best=p.score
        frontier=original.pareto_frontier(points)
        assert set(frontier)==set(scan)
        zoom=(-0.08,4.8) if platform=='Copilot' else (-0.08,13.2)
        cfg=dict(version='2.1',ylim=(20,65),ytop=65,zoom=zoom,split=4.7 if platform=='Copilot' else 13.0,
                 title=f'{platform}: AA Coding Agent Index v2.1 - REFERENCE ONLY',
                 subtitle=f'{DATE} (Asia/Taipei) | {len(points)} verified model/effort points | AA API cost, NOT platform billing | Linear axes',
                 xlabel='AA API cost per Coding Agent task (USD) - reference only',
                 ylabel='AA Coding Agent Index v2.1',
                 note1='Black line: AA API-cost reference Pareto only; platform task credits unknown for every point.',
                 note2='Mixed harnesses are explicitly identified in CSV. No platform-native inference. All pricing tiers: platform_cost_layer CSV.',
                 footer='AA v2.1: FrontierCode-AA 2.0 + Terminal-Bench 4.1 + SWE-Atlas-QnA-AA. Official sources, promotions, pending efforts: README.',
                 stem=str(DATA/f'{platform.lower()}_coding_reference_{DATE}_linear'))
        result=original.plot(points,DATE,cfg)
        stem=Path(cfg['stem'])
        with Image.open(stem.with_suffix('.png')) as im:im.verify()
        result.update(formal_platform_frontier_complete=False,formal_points=0,reference_points=len(points),cost_definition='AA API USD per Coding Agent task; NOT Copilot/Kiro billed task cost',independent_frontier_check=True,original_plotter=True)
        for ext in ['png','svg']:
            result[ext+'_sha256']=hashlib.sha256(stem.with_suffix('.'+ext).read_bytes()).hexdigest()
        report[platform]=result
    (DATA/f'validation_{DATE}.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:{field:v[field] for field in ('reference_points','formal_points','linear_axes','label_overlaps','clipped_labels')} for k,v in report.items()},indent=2))

if __name__=='__main__':run()
