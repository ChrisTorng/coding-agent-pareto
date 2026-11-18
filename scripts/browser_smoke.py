import json
from playwright.sync_api import sync_playwright
from pathlib import Path
root=Path(__file__).resolve().parents[1]
html=(root/'web'/'index.html').read_text().replace('<link rel="stylesheet" href="./style.css">','<style>'+(root/'web'/'style.css').read_text()+'</style>').replace('<script src="./app.js" defer></script>','<script>const stored={};Object.defineProperty(window,"localStorage",{value:{getItem:k=>stored[k]||null,setItem:(k,v)=>{stored[k]=v}}});window.fetch=async()=>({ok:true,json:async()=>('+json.dumps(json.loads((root/'dist/site/data.json').read_text()),ensure_ascii=False)+')})</script><script>'+(root/'web/app.js').read_text()+'</script>')
with sync_playwright() as pw:
    b=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    p=b.new_page(viewport={'width':1700,'height':1000},accept_downloads=True)
    errors=[]
    p.on('pageerror', lambda e:errors.append(str(e)))
    p.set_content(html,wait_until='load');p.locator('#chart-area svg').wait_for()
    assert p.locator('#platform-heading').inner_text()=='GitHub Copilot'
    assert p.locator('.svg-panel').count()==1
    assert p.locator('#providers .children:visible').count()==0, 'Default collapse all vendors'
    assert p.locator('#benchmark-picker').input_value()=='AA Coding Agent Index'
    assert p.locator('#snapshot-picker option:checked').inner_text()=='v2.1 (2026-11-18)'
    assert p.locator('#benchmark-sources a').count()>=2
    assert p.locator('#pricing-sources a').count()>=3
    p.locator('#expand-all').click()
    assert p.locator('#providers .children:visible').count()>=3
    p.locator('input[aria-label="Model GPT-6.2 Sol"]').uncheck()
    assert p.locator('input[aria-label="All models for OpenAI"]').evaluate('(e)=>e.indeterminate')
    p.locator('#collapse-all').click()
    assert p.locator('#providers .children:visible').count()==0
    p.locator('#select-all').click();p.locator('#exclude-china').click()
    assert '44/' in p.locator('#filter-total').inner_text()
    p.locator('#select-all').click()
    p.locator('#cost-scale').select_option('log')
    assert 'log' in p.locator('#axis-summary').inner_text()
    assert p.locator('.svg-point').count()==25
    assert p.locator('#x-min').get_attribute('min')!='0'
    p.locator('#cost-scale').select_option('linear')
    p.locator('#x-max-value').fill('2.0');p.locator('#x-max-value').press('Tab')
    assert '2.00' in p.locator('#axis-summary').inner_text()
    p.locator('#y-min-value').fill('50');p.locator('#y-min-value').press('Tab')
    assert p.locator('.svg-point').count() < 25
    # one track with two handles; validate that both ends update selected track
    assert p.locator('#x-dual input[type=range]').count()==2 and p.locator('#y-dual input[type=range]').count()==2
    assert p.locator('#x-dual').evaluate('(e)=>e.style.getPropertyValue("--hi")')
    p.locator('#reset-range').click()
    before=p.locator('#x-max-value').input_value()
    grip=p.locator('#x-max-grip');grip.scroll_into_view_if_needed();bb=grip.bounding_box();xx=bb['x']+bb['width']/2;yy=bb['y']+bb['height']/2
    p.mouse.move(xx,yy);p.mouse.down();p.mouse.move(xx-120,yy,steps=10);p.mouse.up()
    assert float(p.locator('#x-max-value').input_value()) < float(before), 'X high handle must respond to a real pointer drag'
    prior=float(p.locator('#y-min-value').input_value())
    grip=p.locator('#y-min-grip');grip.scroll_into_view_if_needed();bb=grip.bounding_box();xx=bb['x']+bb['width']/2;yy=bb['y']+bb['height']/2
    p.mouse.move(xx,yy);p.mouse.down();p.mouse.move(xx,yy-45,steps=10);p.mouse.up()
    assert float(p.locator('#y-min-value').input_value()) > prior, 'Y low handle must respond to a real pointer drag'
    p.locator('#reset-range').click()
    p.locator('#hide-filters').click()
    assert p.locator('#filters').is_hidden()
    assert json.loads(p.evaluate('localStorage.getItem("coding-agent-pareto.sidebar.v1")'))['hidden']
    # Storage state is verified directly; real-origin reload is verified after deployment.
    p.locator('#show-filters').click()
    assert p.locator('#filters').is_visible()
    p.locator('#sidebar-resizer').press('ArrowRight')
    assert json.loads(p.evaluate('localStorage.getItem("coding-agent-pareto.sidebar.v1")'))['width']==295
    p.locator('#benchmark-picker').select_option('DeepSWE')
    assert 'v1.1' in p.locator('#snapshot-picker option:checked').inner_text()
    assert p.locator('.svg-point').count()==6
    p.locator('#benchmark-sources a').count()>=1
    p.get_by_role('button',name='Kiro',exact=True).click()
    assert p.locator('#platform-heading').inner_text()=='Kiro'
    assert p.locator('#pricing-sources a').count()>=3
    p.get_by_role('button',name='Claude Code',exact=True).click()
    assert p.locator('#platform-heading').inner_text()=='Claude Code'
    p.locator('#fullscreen-toggle').click()
    assert p.evaluate('!!document.fullscreenElement')
    assert not p.locator('#reference-info').evaluate('(e)=>document.fullscreenElement.contains(e)')
    assert p.locator('#label-mode option').count()==2
    dims=p.evaluate('''() => {const card=document.fullscreenElement,r=document.getElementById('x-dual').getBoundingClientRect(),sr=document.querySelector('#chart-area svg').getBoundingClientRect();return {bodyHeight:card.scrollHeight,viewport:innerHeight,axisBottom:r.bottom,graphTop:sr.top}}''')
    print('Fullscreen:',dims)
    assert dims['axisBottom']<=dims['viewport']+2, dims
    p.locator('#fullscreen-toggle').click()
    assert not p.evaluate('!!document.fullscreenElement')
    p.screenshot(path=str(root/'site-preview-v4.png'),full_page=True)
    print('OK: all browser interactions, sources, range scales, sidebar preferences. errors:', errors)
    assert not errors
    b.close()
