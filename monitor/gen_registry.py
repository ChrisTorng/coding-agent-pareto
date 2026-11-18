import json
from pathlib import Path
from urllib.parse import urlsplit
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'dist/site/data.json').read_text())
primary=[]
for platform,entry in data['platform_sources'].items():
 for link in entry['links']:
  url=link['url']
  if url.startswith('https://raw.githubusercontent.com/') or url.startswith('https://github.com/ChrisTorng/'):continue
  primary.append({'category':'platform_models_prices_promos','platform':platform,'label':link['label'],'url':url,'check_on_every_run':True})
base=[('Artificial Analysis: Coding Agent leaderboard','https://artificialanalysis.ai/agents/coding-agents'),('Artificial Analysis: Index and model leaderboard','https://artificialanalysis.ai/'),('Artificial Analysis methodology','https://artificialanalysis.ai/methodology/coding-agents-benchmarking'),('GitHub Copilot Benchmarks (Fusion DeepSWE and Terminal-Bench)','https://benchmarks.github.com/'),('Terminal-Bench project','https://www.tbench.ai/')]
for label,url in base:primary.append({'category':'benchmarks','platform':'cross-platform','label':label,'url':url,'check_on_every_run':True})
urlSeen=set();unique=[]
for v in primary:
 if v['url'] not in urlSeen:unique.append(v);urlSeen.add(v['url'])
secondary=sorted({v['url'] for c in data['charts'] for v in c['sources'] if v['url'].startswith('https://artificialanalysis.ai/') and v['url'] not in urlSeen})
output={'schema_version':1,'source_of_truth':'GitHub Copilot / Kiro / Claude Code primary official sources; benchmark primary leaderboards; checked comparison/model pages only when a primary page indicates new data','source_snapshot_date':'2026-11-18','policy':'Compare prior saved source content/ETag and structured facts. Fetch secondary complete model/effort/score/cost data when a primary source contains a material update. Preserve history, include all vendor countries, do not fabricate missing scores. A markup-only change is not a model price or benchmark change. The monitoring ChatGPT automation is responsible for interpretation and committing; GitHub Actions only builds/redeploys committed data.','primary_sources':unique,'conditional_detail_sources':secondary,'private_or_repo_sources_are_not_external_checks':True}
(root/'monitor/source_registry.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print(len(unique),'primary and',len(secondary),'conditional detail sources')