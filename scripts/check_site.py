"""Validate the static site and all known snapshot datasets without inventing benchmark values."""
import json
from pathlib import Path
p = Path('dist/site')
for asset in ('index.html', 'style.css', 'app.js', 'data.json', '.nojekyll'):
    assert (p/asset).is_file(), f'Missing {asset}'
d = json.loads((p/'data.json').read_text(encoding='utf-8'))
assert len(d['charts']) >= 13, 'Missing historical benchmark snapshots'
assert len(d['catalog']) >= 50, 'Model catalog too small'
assert any(m['model'].startswith('MAI Code 2') for m in d['catalog']), 'Missing new MAI models'
assert all(next(m for m in d['catalog'] if m['model']==name)['rate']['output'] == output for name,output in [('MAI Code 2',2.5),('MAI Code 2 Flash',0.25)]), 'Missing promotional MAI rates'
neon=next(m for m in d['catalog'] if m['model']=='Gemini 4 Neon')
assert neon['platforms']['Copilot']['rate']['input']==3 and neon['platforms']['Copilot']['rate']['cached_input']==0.15 and neon['platforms']['Copilot']['rate']['output']==15
fable=next(m for m in d['catalog'] if m['model']=='Claude Fable 5.2')
assert fable['platforms']['Claude Code']['rate']['input']==8 and fable['platforms']['Claude Code']['rate']['output']==40
# Official November 20 inventories and versioned score snapshots
from pathlib import Path as _Path
assert any(c['version']=='5.0.1' and c['benchmark']=='AA Intelligence Index' for c in d['charts']), 'Missing current AA Intelligence v5.0.1'
assert any(c['version']=='4.1' and c['benchmark']=='Terminal-Bench' for c in d['charts']), 'Missing independent TB 4.1'
assert any(c.get('cost_unit')=='USD/full_submission_rounded' for c in d['charts']), 'TB total cost must not be reported as USD/task'
assert len(json.loads(_Path('copilot_pareto/terminal_bench/terminal_bench_v4_1_2026-11-20.json').read_text())['records'])==66
assert len(json.loads(_Path('copilot_pareto/v5/intelligence_index_v5_0_1_2026-11-20.json').read_text())['rows'])==28
assert len(json.loads(_Path('monitor/copilot_available_2026-11-20.json').read_text())['models'])==34
assert len(json.loads(_Path('monitor/copilot_prices_2026-11-20.json').read_text())['rows'])==48
assert len(json.loads(_Path('monitor/kiro_available_2026-11-20.json').read_text())['models'])==25
assert next(m for m in d['catalog'] if m['model']=='Gemini 4 Neon')['platforms']['Copilot']['rate']['output']==15
assert any(m['model']=='GLM-5' and m['platforms'].get('Kiro') for m in d['catalog'])
assert any(m['china'] for m in d['catalog']), 'China models must exist for default-all and exclusion controls'
assert any(not m['china'] for m in d['catalog']), 'Missing non-China models'
assert set(['Copilot','Kiro','Claude Code']).issubset({p for c in d['charts'] for p in c['platforms']})
assert all(m['country']!='Unknown' for m in d['catalog']), 'Provider country missing'
assert any(c['benchmark'] == 'AA Intelligence Index' for c in d['charts']), 'Missing old AA Intelligence history'
assert set(['aa_coding_agent_v21','aa_coding_agent_v20','fusion_deepswe_11','fusion_terminal_bench_40']).issubset({c['id'] for c in d['charts']})
assert all(c['points'] for c in d['charts']), 'Missing benchmark points'
assert all(0 <= pt['score'] <= 100 and pt['cost'] >= 0 for c in d['charts'] for pt in c['points']), 'Invalid score/cost'
for chartid,files in d['static_charts'].items():
    for fmt in ('png','svg'):
        assert fmt in files, (chartid,fmt)
        assert (p/files[fmt].replace('./','')).is_file(), (chartid,fmt)
js=(p/'app.js').read_text(encoding='utf-8')
assert 'eligibleScoredKeys' in js and 'keys.has(key(m))' in js, 'Unscored models must be hidden from left selector'
for text in ('exclude-china','select-all','benchmark-picker','snapshot-picker','range-mode','point-mode','collapse-all','expand-all','hide-filters','sidebar-resizer','model-search','svg','export-action','catalog-rows','fullscreen-toggle'):
    assert text in js, f'Missing control: {text}'
assert 'https://github.com/ChrisTorng/coding-agent-pareto' in (p/'index.html').read_text(encoding='utf-8')
assert 'https://christorng.idv.tw/' in (p/'index.html').read_text(encoding='utf-8')
print(json.dumps({'charts':len(d['charts']),'catalog_models':len(d['catalog']),'china_models':sum(m['china'] for m in d['catalog']),'benchmark_points':sum(len(c['points']) for c in d['charts']),'static_images':sum(len(v) for v in d['static_charts'].values())},indent=2))

html=(p/'index.html').read_text(encoding='utf-8')
for x in ('x-max-value','y-min-value','platform-full','fullscreen-toggle','export-kind','benchmark-picker','snapshot-picker','range-mode','point-mode','collapse-all','expand-all','hide-filters','show-filters','sidebar-resizer','x-dual','y-dual','x-min-grip','x-max-grip','y-min-grip','y-max-grip','benchmark-sources','pricing-sources'):
    assert f'id="{x}"' in html, f'Missing UI: {x}'

assert d.get('data_update_mode') == 'frozen-reviewed-snapshots', 'Never describe reviewed 2026 snapshots as live price polling'
assert d['audit']['primary_total']>=18 and d['audit']['directly_checked']<d['audit']['primary_total'], 'Audit must disclose incomplete source coverage'
assert set(d.get('platform_sources',{})) == {'Copilot','Kiro','Claude Code'}
for platform,info in d['platform_sources'].items():
    assert len(info['links']) >= 2 and all(link['url'].startswith('https://') for link in info['links']), platform
for c in d['charts']:
    assert c['sources'] and all(s['url'].startswith('https://') for s in c['sources']), c['id']
    assert c['version'] and c['snapshot'] and c['benchmark'], c['id']
print('Historical benchmark and price source links: validated')

# Keep all references outside fullscreen, and document query-string/model preferences.
page=(p/'index.html').read_text(encoding='utf-8')
assert page.index('id="reference-info"') > page.index('id="chart-card"'), 'References must be after plot'
assert page.count('id="promo-line"')==1 and page.count('id="benchmark-sources"')==1
assert page.count('id="scale-explainer"')==1
assert 'id="label-mode" type="checkbox"' in page
assert 'name="cost-scale" value="linear"' in page and 'name="cost-scale" value="log"' in page
for token in ('range-mode','point-mode','pareto-labels'):
    assert f'id="{token}"' in page, token
for token in ('vendorShape','modelHue','showSeries','clearSeries','latestChart','autoBounds'):
    assert token in js, token
assert page.index('id="export-action"') > page.index('id="reference-info"'), 'Export must stay out of fullscreen'
for token in ('writeQuery','restoreQuery','saveExclusions','logFloor','niceStep'):
    assert token in js, token

registry=Path('monitor/source_registry.json')
assert registry.exists(), 'Missing external source monitoring registry'
watch=json.loads(registry.read_text(encoding='utf-8'))
assert len(watch['primary_sources'])>=18 and len(watch['conditional_detail_sources'])>=72
assert any('version=4.1' in x['url'] for x in watch['primary_sources'])
assert any(x['url']=='https://www.tbench.ai/news' for x in watch['primary_sources'])
assert all(x['url'].startswith('https://') for x in watch['primary_sources'])
assert not any('raw.githubusercontent.com/ChrisTorng' in x['url'] for x in watch['primary_sources'])
print('Source-monitor registry:',len(watch['primary_sources']),'primary /',len(watch['conditional_detail_sources']),'conditional')