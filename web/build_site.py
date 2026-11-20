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
    if 'fusion' in m or m.startswith('raptor'):return 'GitHub'
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
# Incremental rates reviewed on 2026-11-20; preserve the 2026-11-18 baseline.
reviewed_delta=readcsv(SRC/'v21'/'platform_rates_2026-11-20.csv')
for r in reviewed_delta:
 if r.get('platform')=='Copilot':
  addmodel(r['model'],None,r['rate_source'],{'platform':'Copilot',
   'input':num(r.get('input_usd_per_m')), 'cached_input':num(r.get('cached_input_usd_per_m')),
   'cache_write':num(r.get('cache_write_usd_per_m')), 'output':num(r.get('output_usd_per_m')),
   'promo_end':r.get('promo_end',''), 'tier':r.get('tier','default')})
# Official complete Copilot token-rate tiers for this snapshot, replacing earlier partial defaults.
copilot_official=json.loads((ROOT/'monitor/copilot_prices_2026-11-20.json').read_text(encoding='utf-8'))
for r in copilot_official['rows']:
    model=r['model']; provider=r['provider']; source=r['source_url']
    addmodel(model,provider,source)
    entry=catalog[(provider_for(model,provider),model)]
    entry.setdefault('rate_tiers',[]).append({
       'tier':r['tier'],'threshold':r['context_threshold'],
       'input':r['input_usd_per_m'],'cached_input':r['cached_input_usd_per_m'],
       'cache_write':r['cache_write_usd_per_m'],'output':r['output_usd_per_m'],
       'promo_end':r['promo_end']})
    if r['tier'].lower()=='default':
       entry['rate']={'platform':'Copilot','input':r['input_usd_per_m'],
           'cached_input':r['cached_input_usd_per_m'],'cache_write':r['cache_write_usd_per_m'],
           'output':r['output_usd_per_m'],'promo_end':r['promo_end'] or '',
           'tier':'promotional' if r['promo_end'] else 'default','source':source}
for v, p in [('v2',SRC/'v2'/'coding_agent_data_2026-10-30.csv'),('v21',SRC/'v21'/'coding_agent_data_2026-11-18.csv')]:
    for r in readcsv(p):addmodel(r.get('model'),r.get('provider'),r.get('source',''))

# Add current published GitHub Copilot catalog models that do not yet have a benchmark record.
# Input prices are promotional where indicated. They will NOT be plotted until a measured score is present.
current={'Microsoft':['MAI Code 2','MAI Code 2 Flash','MAI-Code-1.1-Flash'],'Google':['Gemini 3.8 Flash','Gemini 4 Argon','Gemini 4 Carbon','Gemini 4 Hydrogen','Gemini 4 Neon'],'OpenAI':['GPT-6.2 Astra','GPT-6.2 Sol','GPT-6.1 Terra','GPT-6 Luna'],'Anthropic':['Claude Opus 5.5','Claude Fable 5.2','Claude Sonnet 5.5'],'Moonshot AI':['Kimi K2.7 Code','Kimi K3'],'Alibaba':['Qwen3-Coder'],'DeepSeek':['DeepSeek V3.2'],'Z.ai':['GLM-4.7'],'MiniMax':['MiniMax M2']}
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
# Platform support is platform-specific, not inferred from cross-harness benchmark scores.
# Dates and source URLs are retained so historical entries cannot masquerade as live availability.
COUNTRIES={'OpenAI':'US','Anthropic':'US','Google':'US','Microsoft':'US','GitHub':'US','xAI':'US',
 'Alibaba':'CN','DeepSeek':'CN','Moonshot AI':'CN','MiniMax':'CN','Z.ai':'CN','ByteDance':'CN'}
COPILOT_SOURCE='https://docs.github.com/en/copilot/reference/ai-models/supported-models'
COPILOT_PRICES='https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing'
KIRO_SOURCE='https://kiro.dev/docs/models/available-models/'
KIRO_PRICES='https://kiro.dev/pricing/'
CLAUDE_SOURCE='https://code.claude.com/docs/en/model-config'
CLAUDE_PRICES='https://platform.claude.com/docs/en/about-claude/pricing'
# Official dated inventories, not hand-maintained guesses about supported models.
copilot_inventory=json.loads((ROOT/'monitor/copilot_available_2026-11-20.json').read_text(encoding='utf-8'))
kiro_inventory=json.loads((ROOT/'monitor/kiro_available_2026-11-20.json').read_text(encoding='utf-8'))
claude_inventory=json.loads((ROOT/'monitor/claude_code_models_2026-11-20.json').read_text(encoding='utf-8'))
COPILOT_CURRENT={r['model'] for r in copilot_inventory['models'] if r['release_status'] in ('GA','Public preview')}
kiro_status={r['model']:r['status'] for r in kiro_inventory['models']}
KIRO_CURRENT={name for name,status in kiro_status.items() if status in ('Active','Experimental') and name!='Auto'}
CLAUDE_CURRENT=set(claude_inventory['active_default_models'])
for n in COPILOT_CURRENT:addmodel(n,source=COPILOT_SOURCE)
for n in KIRO_CURRENT:addmodel(n,source=KIRO_SOURCE)
for n in CLAUDE_CURRENT:addmodel(n,source=CLAUDE_SOURCE)
# First-party platform rates, carefully kept separate from benchmark API task estimates.
kiro_rates={}
for r in readcsv(SRC/'v21'/'platform_rates_2026-11-18.csv'):
 if r.get('platform')=='Kiro' and r.get('tier') in ('default','enterprise'):
  kiro_rates[r['model']]={'credits_multiplier':num(r['credit_multiplier']), 'source':r['rate_source'], 'tier':r['tier']}
# Date-reviewed Kiro credit multipliers (missing source values stay unknown).
for r in json.loads((ROOT/'monitor/kiro_multipliers_2026-11-20.json').read_text(encoding='utf-8'))['rates']:
 kiro_rates[r['model']]={'credits_multiplier':r['credit_multiplier'],
    'long_credits_multiplier':r['long_credit_multiplier'],
    'context_threshold_tokens':r['context_threshold_tokens'],
    'tier':'default','source':KIRO_SOURCE}
claude_prices={'Claude Fable 5':(10,50),'Claude Fable 5.1':(10,50),'Claude Opus 5':(5,25),
 'Claude Opus 5.5':(4,20),'Claude Opus 4.8':(5,25),'Claude Opus 4.7':(5,25),'Claude Opus 4.6':(5,25),
 'Claude Sonnet 5':(3,15),'Claude Sonnet 5.5':(2,10),'Claude Haiku 4.5':(1,5)}
# Keep Claude Code API prices separate from the Copilot rate layer.
for r in reviewed_delta:
 if r.get('platform')=='Claude Code':
  claude_prices[r['model']]=(num(r.get('input_usd_per_m')),num(r.get('output_usd_per_m')))
# Complete current Anthropic API token-price tiers, not Copilot billable credit rates.
claude_rate_tiers={}
for r in json.loads((ROOT/'monitor/anthropic_prices_2026-11-20.json').read_text(encoding='utf-8'))['rows']:
 claude_rate_tiers.setdefault(r['model'],[]).append(r)
 if r['tier']=='default':
  claude_prices[r['model']]=(r['input_usd_per_m'],r['output_usd_per_m'])
for (pr,model),m in catalog.items():
 m['country']=COUNTRIES.get(pr,'Unknown')
 m['platforms']={}
 if model in COPILOT_CURRENT or m.get('rate',{} ) and m['rate'].get('platform')=='Copilot':
  m['platforms']['Copilot']={'status':'documented / benchmark-era','source':COPILOT_SOURCE,'pricing_source':COPILOT_PRICES,
   'rate':m['rate'] if m.get('rate') and m['rate'].get('platform')=='Copilot' else None}
 if model in KIRO_CURRENT:
  m['platforms']['Kiro']={'status':kiro_status.get(model,'Unverified')+(' (multiplier available)' if model in kiro_rates else ' (multiplier unavailable)'),
   'source':KIRO_SOURCE,'pricing_source':KIRO_PRICES,'rate':kiro_rates.get(model)}
 if model in CLAUDE_CURRENT:
  inp,out=claude_prices.get(model,(None,None))
  m['platforms']['Claude Code']={'status':'documented / historical' if inp is None else 'documented',
   'source':CLAUDE_SOURCE,'pricing_source':CLAUDE_PRICES,
   'rate':({'input':inp,'output':out,'tier':'API','platform':'Claude Code',
       'cached_input':(claude_rate_tiers.get(model) or [{}])[0].get('cached_input_usd_per_m'),
       'cache_write_5m':(claude_rate_tiers.get(model) or [{}])[0].get('cache_write_5m_usd_per_m'),
       'rate_tiers':claude_rate_tiers.get(model,[])} if inp is not None else None)}

# AA scored examples for Kiro and native Claude Code harness are preserved on separate platform tabs.
for ver,srcfile in [('2.1',SRC/'v21'/'coding_agent_data_2026-11-18.csv'),('2.0',SRC/'v2'/'coding_agent_data_2026-10-30.csv')]:
 for platform in ('Kiro','Claude Code'):
  pts=[]
  for r in readcsv(srcfile):
   if platform=='Kiro':
    if r.get('platform')!='Kiro' or r.get('reference_included')!='True':continue
   else:
    if r.get('platform')!='Copilot' or r.get('harness')!='Claude Code' or r.get('provider')!='Anthropic':continue
   model=r.get('model'); score=num(r.get('score')); cost=num(r.get('api_cost_usd_task'))
   if score is None or cost is None:continue
   pt=record_to_point(model,r.get('provider'),r.get('effort'),score,cost,r.get('source'),r.get('harness'))
   if pt:pts.append(pt)
  if pts:
   chartid=('kiro' if platform=='Kiro' else 'claude_code')+'_aa_v'+ver.replace('.','')
   charts.append({'id':chartid,'label':'AA Coding Agent Index v'+ver,
     'snapshot':'2026-11-18' if ver=='2.1' else '2026-10-30', 'version':ver,
     'benchmark':'AA Coding Agent Index', 'platforms':[platform], 'cost_basis':'AA cross-harness reference, USD/task',
     'points':pts,'zoom_max':4.8 if ver=='2.1' else 3.2})
# Append new, independently versioned datasets. Only current platform-verified models enter plots;
# raw official tables retain every row and unscored vendor for future monitoring.
v5_snapshot=json.loads((SRC/'v5'/'intelligence_index_v5_0_1_2026-11-20.json').read_text(encoding='utf-8'))
tb41_snapshot=json.loads((SRC/'terminal_bench'/'terminal_bench_v4_1_2026-11-20.json').read_text(encoding='utf-8'))
verified_platforms={'Copilot':COPILOT_CURRENT,'Kiro':KIRO_CURRENT,'Claude Code':CLAUDE_CURRENT}
for platform,allowed in verified_platforms.items():
    prefix={'Copilot':'','Kiro':'kiro_','Claude Code':'claude_code_'}[platform]
    v5_points=[]
    for r in v5_snapshot['rows']:
        if r['model'] not in allowed:continue
        point=record_to_point(r['model'],r['provider'],r['effort'],num(r['score']),
            num(r['cost_usd_task']),r['source'],'Official AA model evaluation (not platform-native)')
        if point:v5_points.append(point)
    if v5_points:
        charts.append({'id':prefix+'intelligence_v5_0_1_2026-11-20',
          'label':'AA Intelligence Index v5.0.1 (official featured results)',
          'snapshot':'2026-11-20','version':'5.0.1','benchmark':'AA Intelligence Index',
          'platforms':[platform], 'cost_basis':'Official AA v5.0.1 API USD/task; featured selection, not all evaluated variants',
          'coverage_note':'Featured public results only: '+str(len(v5_snapshot['rows']))+' source variants; other official results not verified',
          'points':v5_points,'zoom_max':5})
    tb_points=[]
    for r in tb41_snapshot['records']:
        if r['model'] not in allowed:continue
        cost=num(r.get('cost_total_usd_rounded'))
        # Official total is rounded to $0.1k; $0.0k is not a verified zero.
        if cost is None or cost<=0:continue
        p=record_to_point(r['model'],None,r['effort'],num(r['resolution_rate_pct']),
            cost,r['source_url'],r['agent'])
        if p:
            p['official_cost_label']=r['cost_total_raw']
            p['confidence_interval']=r['confidence_interval_raw']
            tb_points.append(p)
    if tb_points:
        charts.append({'id':prefix+'terminal_bench_v4_1_2026-11-20',
          'label':'Terminal-Bench 4.1 — official results (rounded total run cost)',
          'snapshot':'2026-11-20','version':'4.1','benchmark':'Terminal-Bench',
          'platforms':[platform], 'cost_basis':'Official total cost for entire submission, rounded to $100; NOT USD/task; agent/harness may differ from selected platform',
          'cost_unit':'USD/full_submission_rounded','separate_agents':True,
          'coverage_note':'Raw official leaderboard includes '+str(len(tb41_snapshot['records']))+' entries; display filters to current models with nonzero reported cost',
          'points':tb_points,'zoom_max':3500})
for c in charts:
 c.setdefault('platforms',['Copilot'])
 c.setdefault('cost_basis','Benchmark API estimate, USD/task')
 c['points']=[dict(p, country=COUNTRIES.get(p['provider'],'Unknown')) for p in c['points']]
# Source provenance for each historical series (published benchmark pages and repository CSV/JSON).
# No source below is a live scraping endpoint or an assertion that prices update automatically.
REPO='https://github.com/ChrisTorng/coding-agent-pareto'
RAW='https://raw.githubusercontent.com/ChrisTorng/coding-agent-pareto/main'
def source(label,url): return {'label':label,'url':url}
def benchmark_sources(c):
    b=c['benchmark']; id=c['id']; result=[]
    if b=='AA Coding Agent Index':
        result=[source('Artificial Analysis: Coding Agent leaderboard','https://artificialanalysis.ai/agents/coding-agents'),
                source('Official benchmark methodology','https://artificialanalysis.ai/methodology/coding-agents-benchmarking')]
    elif b=='AA Intelligence Index':
        result=[source('Artificial Analysis: model Intelligence leaderboard','https://artificialanalysis.ai/models'),
                source('Repository historical snapshot files',REPO+'/tree/main/copilot_pareto')]
    elif b=='DeepSWE':
        result=[source('GitHub Copilot benchmarks','https://benchmarks.github.com/')]
    elif b=='Terminal-Bench':
        result=[source('GitHub Copilot benchmarks','https://benchmarks.github.com/'),
                source('Terminal-Bench project','https://www.tbench.ai/')]
    # Preserve the original per-point sources; these may be agent harness comparisons, not native platform scores.
    for url in sorted({p.get('source','') for p in c['points'] if p.get('source','').startswith('https://')}):
        if url not in {r['url'] for r in result}: result.append(source('Original result / comparison',url))
    if id.startswith('aa_coding_agent_v21') or id=='kiro_aa_v21' or id=='claude_code_aa_v21':
        result.append(source('Download frozen v2.1 CSV',RAW+'/copilot_pareto/v21/coding_agent_data_2026-11-18.csv'))
    elif id.startswith('aa_coding_agent_v20') or id=='kiro_aa_v20' or id=='claude_code_aa_v20':
        result.append(source('Download frozen v2.0 CSV',RAW+'/copilot_pareto/v2/coding_agent_data_2026-10-30.csv'))
    elif id in ('fusion_deepswe_11','fusion_terminal_bench_40'):
        result.append(source('Download reviewed comparison CSV',RAW+'/copilot_pareto/four_charts_2026-11-18/four_chart_points_2026-11-18.csv'))
    elif 'intelligence_v5_0_1' in id:
        result.append(source('Official v5.0.1 featured raw snapshot',RAW+'/copilot_pareto/v5/intelligence_index_v5_0_1_2026-11-20.json'))
    elif 'terminal_bench_v4_1' in id:
        result.append(source('Official Terminal-Bench 4.1 full leaderboard',RAW+'/copilot_pareto/terminal_bench/terminal_bench_v4_1_2026-11-20.json'))
    elif id.startswith('intelligence_'):
        date=c['snapshot']; file='copilot_pareto_data.csv' if id.endswith('-csv') else 'source_snapshot_'+date+'.json'
        result.append(source('Download historical snapshot',RAW+'/copilot_pareto/'+file))
    return result
for c in charts: c['sources']=benchmark_sources(c)
PLATFORM_SOURCES={
 'Copilot':{'snapshot':'2026-11-20','update_method':'Reviewed CSV; not automatically refreshed', 'links':[
    source('GitHub: Supported Copilot models','https://docs.github.com/en/copilot/reference/ai-models/supported-models'),
    source('GitHub: Model prices and promotions','https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing'),
    source('GitHub: Fusion discount and billing','https://docs.github.com/en/copilot/concepts/models/copilot-fusion'),
    source('Download reviewed platform rates (CSV)',RAW+'/copilot_pareto/v21/platform_rates_2026-11-18.csv'),
    source('Official Nov 20 complete Copilot rates',RAW+'/monitor/copilot_prices_2026-11-20.json'),
     source('Download 2026-11-20 rate delta',RAW+'/copilot_pareto/v21/platform_rates_2026-11-20.csv')]},
 'Kiro':{'snapshot':'2026-11-20','update_method':'Reviewed model multipliers; not automatically refreshed','links':[
    source('Kiro: Available models and credit multipliers','https://kiro.dev/docs/models/available-models/'),
    source('Kiro: Pricing and plans','https://kiro.dev/pricing/'),
    source('Kiro: Model changes','https://kiro.dev/changelog/models/'),
    source('Official Nov 20 model inventory',RAW+'/monitor/kiro_available_2026-11-20.json'),
    source('Reviewed Nov 20 multipliers',RAW+'/monitor/kiro_multipliers_2026-11-20.json'),
    source('Download reviewed platform rates (CSV)',RAW+'/copilot_pareto/v21/platform_rates_2026-11-18.csv')]},
 'Claude Code':{'snapshot':'2026-11-20','update_method':'Reviewed documentation; not automatically refreshed','links':[
    source('Claude Code: Model selection','https://code.claude.com/docs/en/model-config'),
    source('Anthropic: API pricing','https://platform.claude.com/docs/en/about-claude/pricing'),
    source('Claude Code: Usage and costs','https://code.claude.com/docs/en/costs'),
    source('Reviewed Nov 20 API price tiers',RAW+'/monitor/anthropic_prices_2026-11-20.json'),
    source('Download benchmark source CSV',RAW+'/copilot_pareto/v21/coding_agent_data_2026-11-18.csv'),
     source('Download 2026-11-20 rate delta',RAW+'/copilot_pareto/v21/platform_rates_2026-11-20.csv')]},
}
# Deduplicate models but preserve multiple effort points and all snapshots.
D={'generated_from':'Versioned Copilot Pareto repository snapshots','catalog':sorted(catalog.values(),key=lambda r:(r['provider'],r['model'])),'charts':charts,'static_charts':static,'promos':promos,'last_snapshot':'2026-11-20','repository':'https://github.com/ChrisTorng/coding-agent-pareto','platform_sources':PLATFORM_SOURCES,'data_update_mode':'frozen-reviewed-snapshots'}
(DEST/'data.json').write_text(json.dumps(D,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
for name in ('index.html','app.js','style.css'):
    shutil.copy2(WEB/name,DEST/name)
(DEST/'.nojekyll').write_text('',encoding='utf-8')
print(json.dumps({'charts':{x['id']:len(x['points']) for x in charts},'catalog':len(catalog),'china':sum(x['china'] for x in catalog.values()),'site_files':[x.name for x in DEST.iterdir()]},ensure_ascii=False))