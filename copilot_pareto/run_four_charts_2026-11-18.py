"""Four Copilot Pareto charts; restores the exact approved original light two-panel plotter.

Run: python copilot_pareto/run_four_charts_2026-11-18.py
No image generation. Data from existing audited AA v2.0/v2.1 CSVs and benchmark snapshot CSV.
"""
from __future__ import annotations
import csv
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

from PIL import Image
import plot_copilot_pareto as original

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'four_charts_2026-11-18'
TODAY = '2026-11-18'
FUSION_DISCOUNT = 0.70

# Same footer placement and typography on ALL FOUR figures, via the original plotter.
PROMO_LINE_1 = 'COPILOT PROMOS: Fusion -30% through 2026-11-30; Auto -10% (Auto is excluded from plotted models).'
PROMO_LINE_2 = 'Gemini 4 Argon/Carbon: -50% through 2026-12-01; Gemini 3.8 Flash: promo through 2026-12-31.'
PROMO_LINE_3 = 'MAI Code 2 / 2 Flash: -50% promotional rates until 2027-05-17. All promotion terms: official GitHub pricing.'

original.COLORS['Router'] = '#7753a5'
original.EFFORT_ORDER['standard'] = -1

def load_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def to_float(x):
    return float(x) if x not in ('',None) else None

def make(points, name, title, score_label, source_note, zoom, split, ylim, version):
    assert points and len({(p.model,p.effort) for p in points})==len(points)
    assert all(p.cost > 0 and p.score >= 0 for p in points)
    cfg={
      'version': version,
      'ylim': ylim,
      'ytop': int(ylim[1]) // 5 * 5,
      'zoom': zoom,
      'split': split,
      'title': title,
      'subtitle': f'{TODAY} (Asia/Taipei)  |  {len(points)} model/effort variants  |  {source_note}  |  Linear X axes',
      'xlabel': 'Estimated cost per benchmark task (USD; linear)',
      'ylabel': score_label,
      'note1': PROMO_LINE_1,
      'note2': PROMO_LINE_2,
      'footer': PROMO_LINE_3,
      'frontier_legend': f'Pareto frontier ({len(original.pareto_frontier(points))} points)',
      'label_low_on_full': name != 'aa_coding_agent_v21',
      'stem': str(OUT / f'{name}_{TODAY}_linear'),
    }
    result=original.plot(points, TODAY, cfg)
    stem=Path(cfg['stem'])
    for ext in ('png','svg'):
        assert stem.with_suffix('.'+ext).exists()
        result[ext+'_sha256']=hashlib.sha256(stem.with_suffix('.'+ext).read_bytes()).hexdigest()
    with Image.open(stem.with_suffix('.png')) as im:
        im.verify()
    assert result['linear_axes'] and not result['label_overlaps'] and not result['clipped_labels']
    result['filename']=stem.name
    result['source_note']=source_note
    return result

def p(provider,model,effort,score,cost):
    return original.Point(provider,model,effort,float(score),float(cost),'measured','published',False)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results={}
    consolidated=[]
    for version, fname, zoom, split, ylim in [
        ('2.1','aa_coding_agent_v21',(-0.08,4.8),4.7,(20,65)),
        ('2.0','aa_coding_agent_v20',(-0.07,3.2),3.1,(20,67)),
    ]:
        src=ROOT / ('v21/coding_agent_data_2026-11-18.csv' if version=='2.1' else 'v2/coding_agent_data_2026-10-30.csv')
        rows=[r for r in load_csv(src) if r['platform']=='Copilot' and r['reference_included']=='True']
        assert len(rows)==(25 if version=='2.1' else 15), (version,len(rows))
        points=[]
        for r in rows:
            original_cost=float(r['api_cost_usd_task'])
            fusion = r['model']=='Copilot Fusion'
            # Discounted Fusion benchmark *scenario*; fixed model API proxies left unchanged.
            effective_cost=original_cost * FUSION_DISCOUNT if fusion else original_cost
            points.append(p(r['provider'],r['model'],r['effort'],r['score'],effective_cost))
            consolidated.append({'chart':fname,'version':version,'benchmark':'AA Coding Agent Index','model':r['model'],'effort':r['effort'],
                'provider':r['provider'],'harness':r['harness'],'score':r['score'],'source_estimate_cost_usd':f'{original_cost:.4f}',
                'discount_factor':f'{FUSION_DISCOUNT:.2f}' if fusion else '1.00','plotted_estimate_cost_usd':f'{effective_cost:.4f}',
                'promotion':'Fusion -30% to 2026-11-30' if fusion else '', 'source':r['source']})
        name=f'{fname}'
        suffix=' (Fusion max plotted at 30% off)' if version=='2.0' else ' (Fusion not measured in AA v2.1)'
        results[name]=make(points,name,f'GitHub Copilot model / effort Pareto frontier - AA Coding Agent Index v{version}',
            f'AA Coding Agent Index v{version} score', 'AA API task-cost reference'+suffix,zoom,split,ylim,version)

    bench = load_csv(OUT/'benchmark_snapshot_and_discount_sensitivity.csv')
    for bname,fname,zoom,split,ylim in [
        ('DeepSWE 1.1','fusion_deepswe_11',(-0.03,1.17),1.13,(60,83)),
        ('Terminal-Bench 4.0','fusion_terminal_bench_40',(-0.08,3.0),2.95,(15,73)),
    ]:
        rows=[r for r in bench if r['benchmark']==bname]
        assert len(rows)==6,(bname,len(rows))
        points=[]
        for r in rows:
            model_raw=r['model']
            fusion=model_raw.startswith('Fusion ')
            if fusion:
                model='Copilot Fusion'; effort=model_raw.removeprefix('Fusion ').lower(); provider='Router'
            else:
                model, effort=model_raw.rsplit(' / ',1)
                provider='Anthropic' if model.startswith('Claude') else 'OpenAI'
            reported_cost=float(r['reported_estimate_usd_per_task'])
            effective_cost=reported_cost*FUSION_DISCOUNT if fusion else reported_cost
            points.append(p(provider,model,effort,r['success_rate_percent'],effective_cost))
            consolidated.append({'chart':fname,'version':bname,'benchmark':bname,'model':model,'effort':effort,
                'provider':provider,'harness':'GitHub Benchmarks (third-party snapshot)','score':r['success_rate_percent'],
                'source_estimate_cost_usd':f'{reported_cost:.4f}',
                'discount_factor':f'{FUSION_DISCOUNT:.2f}' if fusion else '1.00',
                'plotted_estimate_cost_usd':f'{effective_cost:.4f}',
                'promotion':'Fusion -30% to 2026-11-30' if fusion else '',
                'source':'https://zenn.dev/mochan_tk/articles/2caab47932dd9e'})
        results[fname]=make(points,fname,f'GitHub Copilot Fusion vs fixed models - {bname}',
            f'{bname} success rate (%)', '2026-11-08 third-party benchmark snapshot; Fusion cost x 0.70',
            zoom,split,ylim,bname)

    with (OUT/'four_chart_points_2026-11-18.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(consolidated[0]));writer.writeheader();writer.writerows(consolidated)
    (OUT/'validation_2026-11-18.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:{'points':v['plotted_points'],'frontier':len(v['frontier']), 'overlaps':v['label_overlaps'],'clipped':v['clipped_labels']} for k,v in results.items()},indent=2))

if __name__=='__main__': main()
