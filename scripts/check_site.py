"""Validate the static site and all known snapshot datasets without inventing benchmark values."""
import json
from pathlib import Path
p = Path('dist/site')
for asset in ('index.html', 'style.css', 'app.js', 'data.json', '.nojekyll'):
    assert (p/asset).is_file(), f'Missing {asset}'
d = json.loads((p/'data.json').read_text(encoding='utf-8'))
assert len(d['charts']) >= 7, 'Missing historical benchmark snapshots'
assert len(d['catalog']) >= 50, 'Model catalog too small'
assert any(m['model'].startswith('MAI Code 2') for m in d['catalog']), 'Missing new MAI models'
assert all(next(m for m in d['catalog'] if m['model']==name)['rate']['output'] == output for name,output in [('MAI Code 2',2.5),('MAI Code 2 Flash',0.25)]), 'Missing promotional MAI rates'
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
for text in ('exclude-china','select-all','benchmark-picker','snapshot-picker','cost-scale','collapse-all','expand-all','hide-filters','sidebar-resizer','model-search','svg','export-action','catalog-rows','fullscreen-toggle'):
    assert text in js, f'Missing control: {text}'
assert 'https://github.com/ChrisTorng/coding-agent-pareto' in (p/'index.html').read_text(encoding='utf-8')
assert 'https://christorng.idv.tw/' in (p/'index.html').read_text(encoding='utf-8')
print(json.dumps({'charts':len(d['charts']),'catalog_models':len(d['catalog']),'china_models':sum(m['china'] for m in d['catalog']),'benchmark_points':sum(len(c['points']) for c in d['charts']),'static_images':sum(len(v) for v in d['static_charts'].values())},indent=2))

html=(p/'index.html').read_text(encoding='utf-8')
for x in ('x-max-value','y-min-value','platform-full','fullscreen-toggle','export-kind','benchmark-picker','snapshot-picker','cost-scale','collapse-all','expand-all','hide-filters','show-filters','sidebar-resizer','x-dual','y-dual','x-min-grip','x-max-grip','y-min-grip','y-max-grip','benchmark-sources','pricing-sources'):
    assert f'id="{x}"' in html, f'Missing UI: {x}'

assert d.get('data_update_mode') == 'frozen-reviewed-snapshots', 'Never describe reviewed 2026 snapshots as live price polling'
assert set(d.get('platform_sources',{})) == {'Copilot','Kiro','Claude Code'}
for platform,info in d['platform_sources'].items():
    assert len(info['links']) >= 2 and all(link['url'].startswith('https://') for link in info['links']), platform
for c in d['charts']:
    assert c['sources'] and all(s['url'].startswith('https://') for s in c['sources']), c['id']
    assert c['version'] and c['snapshot'] and c['benchmark'], c['id']
print('Historical benchmark and price source links: validated')