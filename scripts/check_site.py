"""Validate the static site and all known snapshot datasets without inventing benchmark values."""
import json
from pathlib import Path
p = Path('dist/site')
for asset in ('index.html', 'style.css', 'app.js', 'data.json', '.nojekyll'):
    assert (p/asset).is_file(), f'Missing {asset}'
d = json.loads((p/'data.json').read_text(encoding='utf-8'))
assert len(d['charts']) >= 7, 'Missing historical benchmark snapshots'
assert len(d['catalog']) >= 40, 'Model catalog too small'
assert any(m['model'].startswith('MAI Code 2') for m in d['catalog']), 'Missing new MAI models'
assert all(next(m for m in d['catalog'] if m['model']==name)['rate']['output'] == output for name,output in [('MAI Code 2',2.5),('MAI Code 2 Flash',0.25)]), 'Missing promotional MAI rates'
assert any(m['china'] for m in d['catalog']), 'China models must exist for default-all and exclusion controls'
assert any(not m['china'] for m in d['catalog']), 'Missing non-China models'
assert any(c['benchmark'] == 'AA Intelligence Index' for c in d['charts']), 'Missing old AA Intelligence history'
assert set(['aa_coding_agent_v21','aa_coding_agent_v20','fusion_deepswe_11','fusion_terminal_bench_40']).issubset({c['id'] for c in d['charts']})
assert all(c['points'] for c in d['charts']), 'Missing benchmark points'
assert all(0 <= pt['score'] <= 100 and pt['cost'] >= 0 for c in d['charts'] for pt in c['points']), 'Invalid score/cost'
for chartid,files in d['static_charts'].items():
    for fmt in ('png','svg'):
        assert fmt in files, (chartid,fmt)
        assert (p/files[fmt].replace('./','')).is_file(), (chartid,fmt)
js=(p/'app.js').read_text(encoding='utf-8')
for text in ('exclude-china','select-all','chart-picker','model-search','svg','export-csv','catalog-rows'):
    assert text in js, f'Missing control: {text}'
assert 'https://github.com/ChrisTorng/coding-agent-pareto' in (p/'index.html').read_text(encoding='utf-8')
assert 'https://christorng.idv.tw/' in (p/'index.html').read_text(encoding='utf-8')
print(json.dumps({'charts':len(d['charts']),'catalog_models':len(d['catalog']),'china_models':sum(m['china'] for m in d['catalog']),'benchmark_points':sum(len(c['points']) for c in d['charts']),'static_images':sum(len(v) for v in d['static_charts'].values())},indent=2))