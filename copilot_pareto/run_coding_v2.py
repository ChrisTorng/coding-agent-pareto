"""Render explicitly separated AA API reference layers using the original plotter.

No platform cost is inferred. Run from any directory with Python.
"""
import csv
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image
import plot_copilot_pareto as original

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'v2'
DATE = '2026-10-30'
BASE = 'https://artificialanalysis.ai/agents/coding-agents/comparisons/'

# Source values are transcribed from the named official comparison tables.
# Total tokens are display-rounded; individual token categories remain unknown.
VALUES = [
 ('Claude Code','Claude Opus 5.5','max',62,56,63,66,11.42,14.5,'claude-code-vs-github-copilot',True),
 ('Claude Code','Claude Sonnet 5.5','max',59,48,66,64,13.30,24.1,'claude-code-vs-github-copilot',True),
 ('Claude Code','Claude Fable 5.1','max',58,49,58,66,11.53,6,'claude-code-vs-github-copilot',True),
 ('Claude Code','Claude Haiku 5.5','max',37,47,31,34,2.67,16.1,'claude-code-vs-github-copilot',False),
 ('GitHub Copilot','Copilot Fusion','max',60,51,71,57,5.59,7.3,'codex-vs-github-copilot',False),
 ('Codex','GPT-6 Astra','max',55,49,56,59,7.04,3.2,'codex-vs-github-copilot',False),
 ('Codex','GPT-6.1 Sol','max',54,49,53,60,1.50,3.9,'codex-vs-github-copilot',False),
 ('Codex','GPT-6.1 Terra','xhigh',48,45,46,54,.69,6.9,'codex-vs-github-copilot',False),
 ('Codex','GPT-6.1 Terra','max',48,42,48,54,1.24,12.3,'codex-vs-github-copilot',False),
 ('Codex','GPT-6.1 Terra','high',46,43,42,53,.54,5.6,'codex-vs-github-copilot',False),
 ('Codex','GPT-6.1 Terra','medium',42,44,35,47,.39,4.1,'codex-vs-github-copilot',False),
 ('Codex','GPT-6.1 Terra','non-reasoning',39,46,25,46,.45,5.8,'codex-vs-github-copilot',False),
 ('Codex','GPT-6.1 Terra','low',35,41,25,39,.20,1.9,'codex-vs-github-copilot',False),
 ('Codex','GPT-6 Luna','max',31,40,16,38,.16,8.9,'codex-vs-github-copilot',False),
 ('Antigravity SDK','Gemini 3.8 Flash','high',33,41,15,44,2.51,14.3,'antigravity-sdk-vs-github-copilot',False),
 ('Grok Build','Grok 4.7','xhigh',47,44,33,63,9.48,15.9,'antigravity-cli-vs-grok-build',False),
 ('Antigravity CLI','Gemini 4 Argon','high',53,49,56,55,None,13.9,'antigravity-cli-vs-github-copilot',False),
 ('Antigravity CLI','Gemini 4 Carbon','high',59,51,64,64,7.74,12.5,'antigravity-cli-vs-github-copilot',False),
]

def run():
 OUT.mkdir(exist_ok=True)
 original.COLORS['Router'] = '#7653b6'
 baseline = json.loads((ROOT/'monitor/baseline_2026-10-30.json').read_text())
 catalog = {r['model'] for r in baseline['copilot']['text_model_tiers']}
 # Commercial Kiro latest-generation models with confirmed AA v2.0 records.
 kiro = {'Claude Opus 5.5','Claude Sonnet 5.5','Claude Fable 5.1','Claude Haiku 5.5'}
 rows = []
 for harness,model,effort,score,fc,tb,swe,cost,tokens,slug,fallback in VALUES:
  provider = 'Anthropic' if model.startswith('Claude') else 'OpenAI' if model.startswith('GPT') else 'Google' if model.startswith('Gemini') else 'xAI' if model.startswith('Grok') else 'Router'
  reason = 'effort availability not confirmed' if effort=='non-reasoning' else 'conflicting API task cost ($5.86 vs $11.73)' if model=='Gemini 4 Argon' else 'not listed by platform' if model=='Gemini 4 Carbon' else ''
  for platform, supported in [('Copilot',model in catalog or model=='Copilot Fusion'),('Kiro',model in kiro)]:
   eligible = supported and not reason
   rows.append(dict(platform=platform,harness=harness,provider=provider,model=model,effort=effort,benchmark='Coding Agent Index',version='2.0',score=score,frontiercode_v1_1=fc,terminal_bench_4_0=tb,swe_atlas_qna_aa=swe,api_cost_usd_task=cost,input_tokens=None,cached_input_tokens=None,cache_write_tokens=None,output_tokens=None,total_tokens_display_m=tokens,platform_cost_task=None,formal_frontier_eligible=False,reference_included=eligible,exclusion_reason=reason if supported else 'not listed by platform',fallback=fallback,score_scope='native' if platform=='Copilot' and harness=='GitHub Copilot' else 'cross-harness reference',source=BASE+slug,checked_at=DATE,measured_at=None))
 # Explicit pending efforts, never silently discarded or inferred.
 for effort in ['standard','high']:
  row=dict(rows[8]);row.update(platform='Copilot',harness='GitHub Copilot',model='Copilot Fusion',provider='Router',effort=effort,score=None,frontiercode_v1_1=None,terminal_bench_4_0=None,swe_atlas_qna_aa=None,api_cost_usd_task=None,total_tokens_display_m=None,reference_included=False,exclusion_reason='AA v2.0 score and model-level token usage not verified',source='https://docs.github.com/en/copilot/concepts/models/copilot-fusion')
  rows.append(row)
 (OUT/f'coding_agent_data_{DATE}.json').write_text(json.dumps(rows,indent=2)+'\n')
 with (OUT/f'coding_agent_data_{DATE}.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 reports={}
 for platform in ['Copilot','Kiro']:
  selected=[r for r in rows if r['platform']==platform and r['reference_included']]
  points=[original.Point(r['provider'],r['model'],r['effort'],r['score'],r['api_cost_usd_task'],'measured','published',r['fallback']) for r in selected]
  assert all(r['version']=='2.0' and r['platform_cost_task'] is None and not r['formal_frontier_eligible'] for r in rows)
  assert len({(r['harness'],r['model'],r['effort']) for r in selected})==len(selected)
  # Independent ordered scan checks the original pairwise dominance implementation.
  scan=[];best=-1
  for p in sorted(points,key=lambda p:(p.cost,-p.score)):
   if p.score>best:scan.append(p);best=p.score
  front=original.pareto_frontier(points)
  assert set(front)==set(scan)
  zoom=(-.05,3.2) if platform=='Copilot' else (2.3,3.1)
  config=dict(version='2.0',ylim=(20,67),ytop=65,zoom=zoom,split=3.1,
   title=f'{platform}: AA v2.0 REFERENCE ONLY - platform frontier pending',
   subtitle=f'{DATE} Asia/Taipei | {len(points)} verified variants | AA API cost, NOT platform billing | Linear axes',
   xlabel='AA API cost per Coding Agent task (USD; reference only)',ylabel='AA Coding Agent Index v2.0',
   note1='Platform effective cost is unknown for every point. Black line: AA API reference frontier only.',
   note2='Harness: Claude=Claude Code; GPT=Codex; Flash=Antigravity SDK; Grok=Grok Build; Fusion=GitHub Copilot.',
   footer='Cross-harness results are not platform-native tests. Missing efforts/costs remain blank. Sources, fallback and availability: CSV / README.',
   stem=str(OUT/f'{platform.lower()}_coding_reference_{DATE}_linear'))
  report=original.plot(points,DATE,config)
  stem=Path(config['stem']);im=Image.open(stem.with_suffix('.png'));im.verify()
  report.update(formal_platform_frontier_complete=False,formal_points=0,reference_points=len(points),cost_definition='AA pay-per-token API reference only',independent_frontier_check=True,png_dimensions=[4140,2052],visual_inspection_passed=False)
  for ext in ['png','svg']:
   report[ext+'_sha256']=hashlib.sha256(stem.with_suffix('.'+ext).read_bytes()).hexdigest()
  reports[platform]=report
 (OUT/f'validation_{DATE}.json').write_text(json.dumps(reports,indent=2)+'\n')
 print(json.dumps({p:{k:r[k] for k in ['reference_points','formal_points','linear_axes','label_count','label_overlaps','clipped_labels']} for p,r in reports.items()},indent=2))

if __name__=='__main__':run()
