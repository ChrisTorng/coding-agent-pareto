#!/usr/bin/env python3
"""Build immutable, chart-selectable browser data from all versioned repository CSV/JSON snapshots.
Only measured points are charted; every catalog model remains selectable even without a benchmark score.
"""
import csv, json, pathlib, re, shutil, os
from collections import defaultdict
ROOT=pathlib.Path(__file__).resolve().parents[1]
SRC=ROOT/'copilot_pareto'; WEB=ROOT/'web'; DEST=ROOT/'dist'/'site'
DEST.mkdir(parents=True,exist_ok=True)
CHINA={'Alibaba','DeepSeek','Moonshot AI','Moonshot','Zhipu AI','Z.ai','MiniMax','ByteDance','Tencent','Baidu','01.AI','StepFun','Qwen','Kimi','GLM','Huawei'}

def provider_for(model, given=None):
    model=str(model or '')
    if given and given not in ('','nan','Router'):
        p=str(given)
        if p in ('Microsoft','GitHub','xAI','OpenAI','Anthropic','Google','Alibaba','DeepSeek','Moonshot AI','MiniMax','ByteDance','Z.ai'):return p
    m=model.lower()
    if 'fusion' in m:return 'GitHub'
    if m.startswith(('gpt','o1','o3','o4','codex')):return 'OpenAI'
    if m.startswith('claude'):return 'Anthropic'
    if m.startswith('gemini'):return 'Google'
    if m.startswith(('mai','phi')):return 'Microsoft'
    if m.startswith('grok'):return 'xAI'
    if m.startswith('qwen'):return 'Alibaba'
    if m.startswith('kimi'):return 'Moonshot AI'
    if m.startswith(('glm','z-ai')):return 'Z.ai'
    if m.startswith('minimax'):return 'MiniMax'
    if m.startswith('deepseek'):return 'DeepSeek'
    if m.startswith(('doubao','seed-')):return 'ByteDance'
    return str(given or 'Other')

def readcsv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def num(v):
    try:
        r=float(v)
        if not (r>=0):return None
        return r
    except (ValueError,TypeError):return None

catalog={}; charts=[]
def addmodel(model,provider=None,source='',rate=None):
    if not model:return
    model=str(model).strip();provider=provider_for(model,provider)
    key=(provider,model)
    if key not in catalog:
        catalog[key]={'provider':provider,'model':model,'china':provider in CHINA,'sources':[],'rate':None}
    if source and source not in catalog[key]['sources']:catalog[key]['sources'].append(source)
    if rate and catalog[key]['rate'] is None:catalog[key]['rate']=rate

def record_to_point(model,provider,effort,score,cost,source='',harness='',base=None):
    addmodel(model,provider,source)
    if score is None or cost is None:return None
    provider=provider_for(model,provider)
    orig=cost if base is None else base
    return {'model':model,'provider':provider,'effort':effort or 'default','score':score,'cost':cost,'base_cost':orig,'discount':round(cost/orig,4) if orig else 1,'source':source,'harness':harness,'china':provider in CHINA}

points_by_chart=defaultdict(list)
for r in readcsv(SRC/'four_charts_2026-11-18'/'four_chart_points_2026-11-18.csv'):
    model=r['model']; pr=r['provider']; addmodel(model,pr,r.get('source'))
    p=record_to_point(model,pr,r['effort'],num(r['score']),num(r['plotted_estimate_cost_usd']),r['source'],r.get('harness',''),num(r['source_estimate_cost_usd']))
    if p:points_by_chart[r['chart']].append(p)

chart_defs=[('aa_coding_agent_v21','AA Coding Agent Index v2.1','2026-11-18','2.1','AA Coding Agent Index'),('aa_coding_agent_v20','AA Coding Agent Index v2.0','2026-10-30','2.0','AA Coding Agent Index'),('fusion_deepswe_11','DeepSWE 1.1 — Fusion vs Fixed Models','2026-11-18','1.1','DeepSWE'),('fusion_terminal_bench_40','Terminal-Bench 4.0 — Fusion vs Fixed Models','2026-11-18','4.0','Terminal-Bench')]
for key,name,date,version,benchmark in chart_defs:
    charts.append({'id':key,'label':name,'snapshot':date,'version':version,'benchmark':benchmark,'points':points_by_chart[key]})

for filename in ['source_snapshot_2026-10-12.json','source_snapshot_2026-10-14.json','source_snapshot_2026-10-28.json']:
    j=json.loads((SRC/filename).read_text(encoding='utf-8'))
    date=j.get('snapshot_date',filename[-15:-5]);ver=j.get('index_version','4.3.2')
    records=[]
    for c in j.get('catalog',[]):addmodel(c.get('model'),c.get('provider'),filename)
    for c in j.get('prices',[]):addmodel(c.get('model'),c.get('provider'),filename)
    for r in j.get('records',[]):
        p=record_to_point(r.get('model'),r.get('provider'),r.get('effort'),num(r.get('score')),num(r.get('cost')),r.get('url',''),r.get('harness',''))
        if p:records.append(p)
    charts.append({'id':'intelligence_'+date,'label':'AA Intelligence Index v'+str(ver)+' — '+date,'snapshot':date,'version':ver,'benchmark':'AA Intelligence Index','points':records})

# Add every historic model/effort as a selectable variant and a separate 2026-10-28 index snapshot.
legacy=[]
for r in readcsv(SRC/'copilot_pareto_data.csv'):
    addmodel(r.get('model'),r.get('provider'),r.get('benchmark_source'))
    if r.get('snapshot_date')=='2026-10-28':
        pt=record_to_point(r.get('model'),r.get('provider'),r.get('effort'),num(r.get('intelligence_index_v4_3_2')),num(r.get('aa_cost_usd_task')),r.get('benchmark_source',''))
        if pt:legacy.append(pt)
if legacy:
    charts.append({'id':'intelligence_2026-10-28-csv','label':'AA Intelligence Index v4.3.2 — 2026-10-28 CSV','snapshot':'2026-10-28','version':'4.3.2','benchmark':'AA Intelligence Index','points':legacy})

# Preserve full Copilot/Kiro model pricing catalog, including all models lacking scored benchmarks.
for r in readcsv(SRC/'v21'/'platform_rates_2026-11-18.csv'):
    addmodel(r.get('model'),None,r.get('rate_source',''),{'platform':r.get('platform'),'input':num(r.get('input_usd_per_m')),'output':num(r.get('output_usd_per_m')),'promo_end':r.get('promo_end',''),'tier':r.get('tier')})
for v, p in [('v2',SRC/'v2'/'coding_agent_data_2026-10-30.csv'),('v21',SRC/'v21'/'coding_agent_data_2026-11-18.csv')]:
    for r in readcsv(p):addmodel(r.get('model'),r.get('provider'),r.get('source',''))

# Add current published GitHub Copilot catalog models that do not yet have a benchmark record.
# Input prices are promotional where indicated. They will NOT be plotted until a measured score is present.
current={'Microsoft':['MAI Code 2','MAI Code 2 Flash','MAI-Code-1.1-Flash'],'Google':['Gemini 3.8 Flash','Gemini 4 Argon','Gemini 4 Carbon','Gemini 4 Hydrogen'],'OpenAI':['GPT-6.2 Astra','GPT-6.2 Sol','GPT-6.1 Terra','GPT-6 Luna'],'Anthropic':['Claude Opus 5.5','Claude Fable 5.2','Claude Sonnet 5.5'],'Moonshot AI':['Kimi K2.7 Code','Kimi K3'],'Alibaba':['Qwen3-Coder'],'DeepSeek':['DeepSeek V3.2'],'Z.ai':['GLM-4.7'],'MiniMax':['MiniMax M2']}
for pr,models in current.items():
    for model in models:addmodel(model,pr,'https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing')
# Official promotional GitHub Copilot token pricing for new, not-yet-benchmarked MAI models.
for model,inp,cached,out in [('MAI Code 2',0.50,0.025,2.50),('MAI Code 2 Flash',0.05,0.005,0.25)]:
    addmodel(model,'Microsoft','https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing',
             {'platform':'Copilot','input':inp,'cached_input':cached,'output':out,'promo_end':'2027-05-17','tier':'promotional'})

promos=[{'label':'Copilot Fusion','discount':'30%','until':'2026-11-30','source':'https://docs.github.com/en/copilot/concepts/models/copilot-fusion'},
{'label':'Gemini 4 Argon / Carbon','discount':'promotional rate','until':'2026-12-01','source':'https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing'},
{'label':'Gemini 3.8 Flash','discount':'promotional rate','until':'2026-12-31','source':'https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing'},
{'label':'MAI Code 2 / MAI Code 2 Flash','discount':'50%','until':'2027-05-17','source':'https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing'}]
# Deploy original Python-rendered images in addition to browser-interactive SVG plots.
static={}
chart_images=SRC/'four_charts_2026-11-18'
imgdest=DEST/'charts';imgdest.mkdir(exist_ok=True)
for id,_,_,_,_ in chart_defs:
    static[id]={}
    for ext in ('png','svg'):
        name=id+'_2026-11-18_linear.'+ext
        src=chart_images/name
        if src.exists():
            shutil.copy2(src,imgdest/name)
            static[id][ext]='./charts/'+name
# These zoom defaults match the fixed four Python production charts.
zoom={'aa_coding_agent_v21':4.8,'aa_coding_agent_v20':3.2,'fusion_deepswe_11':1.6,'fusion_terminal_bench_40':3.0}
for entry in charts:entry['zoom_max']=zoom.get(entry['id'],5)
# Deduplicate models but preserve multiple effort points and all snapshots.
D={'generated_from':'Versioned Copilot Pareto repository snapshots','catalog':sorted(catalog.values(),key=lambda r:(r['provider'],r['model'])),'charts':charts,'static_charts':static,'promos':promos,'last_snapshot':'2026-11-18','repository':'https://github.com/ChrisTorng/coding-agent-pareto'}
(DEST/'data.json').write_text(json.dumps(D,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
for name in ('index.html','app.js','style.css'):
    shutil.copy2(WEB/name,DEST/name)
(DEST/'.nojekyll').write_text('',encoding='utf-8')
print(json.dumps({'charts':{x['id']:len(x['points']) for x in charts},'catalog':len(catalog),'china':sum(x['china'] for x in catalog.values()),'site_files':[x.name for x in DEST.iterdir()]},ensure_ascii=False))