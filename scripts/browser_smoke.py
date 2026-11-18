import subprocess,time,os,json
from playwright.sync_api import sync_playwright
from pathlib import Path
root=Path(__file__).resolve().parents[1]
server=None
html=(root/'web'/'index.html').read_text().replace('<link rel="stylesheet" href="./style.css">', '<style>'+ (root/'web'/'style.css').read_text()+'</style>').replace('<script src="./app.js" defer></script>', '<script>window.fetch=async()=>({ok:true,json:async()=>('+json.dumps(json.loads((root/'dist'/'site'/'data.json').read_text()),ensure_ascii=False)+')})</script><script>'+ (root/'web'/'app.js').read_text()+'</script>')
try:
 time.sleep(.8)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1700,'height':1000},accept_downloads=True)
  errs=[]
  page.on('pageerror',lambda e:errs.append(str(e)))
  page.set_content(html,wait_until='load')
  page.locator('#chart-area svg').wait_for()
  print('START',page.locator('#platform-heading').inner_text(),page.locator('#filter-total').inner_text(), 'points',page.locator('.svg-point').count())
  assert page.locator('.svg-point').count()==25
  assert '56' in page.locator('#filter-total').inner_text() or int(page.locator('#filter-total').inner_text().split('/')[0])>=40
  assert page.locator('.svg-panel').count()==1
  # hierarchical state
  parent=page.locator('input[aria-label="All models for OpenAI"]')
  child=page.locator('input[aria-label="Model GPT-6.2 Sol"]')
  print('BEFORE PARENT',parent.is_checked(), parent.evaluate('(e)=>e.indeterminate'))
  child.uncheck()
  print('AFTER PARENT',parent.is_checked(), parent.evaluate('(e)=>e.indeterminate'))
  assert not parent.is_checked() and parent.evaluate('(e)=>e.indeterminate')
  page.locator('#select-all').click()
  assert parent.is_checked()
  page.locator('#exclude-china').click()
  print('AFTER EXCLUDE',page.locator('#filter-total').inner_text())
  assert page.locator('input[aria-label="All models for Moonshot AI"]').is_checked() is False
  page.locator('#select-all').click()
  # range change cost
  page.locator('#x-max-value').fill('2.0');page.locator('#x-max-value').press('Tab')
  print('AFTER AXIS COST',page.locator('#point-count').inner_text(),page.locator('#axis-summary').inner_text())
  assert '2.00' in page.locator('#axis-summary').inner_text()
  # score axis
  page.locator('#y-min-value').fill('50');page.locator('#y-min-value').press('Tab')
  print('AFTER SCORE',page.locator('#point-count').inner_text())
  assert float(page.locator('#y-min-value').input_value())==50
  # screenshot
  page.screenshot(path=str(root/'site-preview-v3.png'),full_page=True)
  # test export current CSV
  page.select_option('#export-kind','view-csv')
  with page.expect_download() as d:page.locator('#export-action').click()
  print('CSV DOWNLOAD',d.value.suggested_filename)
  # SVG and PNG current view must produce actual downloads.
  for kind,ext in [('view-svg','svg'),('view-png','png')]:
   page.select_option('#export-kind',kind)
   with page.expect_download() as imgdl: page.locator('#export-action').click()
   print('IMAGE DOWNLOAD',kind,imgdl.value.suggested_filename)
   assert imgdl.value.suggested_filename.endswith('.'+ext)
  # original static
  page.select_option('#export-kind','original-png')
  assert not page.locator('#export-kind option[value="original-png"]').is_disabled()
  # Fusion chart
  page.select_option('#chart-picker','fusion_deepswe_11')
  print('FUSION',page.locator('.svg-point').count(),page.locator('#chart-title').inner_text())
  assert page.locator('.svg-point').count()==6
  # platform switching
  page.get_by_role('button',name='Kiro',exact=True).click()
  print('KIRO',page.locator('#platform-heading').inner_text(),page.locator('.svg-point').count(),page.locator('#filter-total').inner_text())
  assert page.locator('#platform-heading').inner_text()=='Kiro'
  assert page.locator('.svg-point').count()>=4
  page.get_by_role('button',name='Claude Code',exact=True).click()
  print('CLAUDE',page.locator('#platform-heading').inner_text(),page.locator('.svg-point').count())
  assert page.locator('.svg-point').count()>=5
  # fullscreen + accessible selectors
  page.locator('#fullscreen-toggle').click()
  page.wait_for_timeout(250)
  print('FULLSCREEN',page.evaluate('!!document.fullscreenElement'),page.locator('#platform-full').is_visible())
  assert page.evaluate('!!document.fullscreenElement')
  page.select_option('#platform-full','Copilot')
  print('FULLSCREEN COPILOT',page.locator('#platform-heading').inner_text())
  assert page.locator('#platform-heading').inner_text()=='GitHub Copilot'
  page.locator('#fullscreen-toggle').click()
  assert not page.evaluate('!!document.fullscreenElement')
  # mobile
  mob=browser.new_page(viewport={'width':390,'height':844},accept_downloads=True)
  mob.set_content(html,wait_until='load');mob.locator('#chart-area svg').wait_for()
  print('MOBILE HORIZONTAL',mob.evaluate('document.documentElement.scrollWidth'),mob.evaluate('innerWidth'))
  mob.screenshot(path=str(root/'site-mobile-v3.png'),full_page=True)
  dark=browser.new_page(viewport={'width':1400,'height':900},color_scheme='dark')
  dark.set_content(html,wait_until='load');dark.locator('#chart-area svg').wait_for();dark.screenshot(path=str(root/'site-dark-v3.png'),full_page=True)
  assert dark.locator('.svg-panel').count()==1
  print('ERRORS',errs)
  assert not errs,errs
  browser.close()
finally:
 if server:server.terminate();server.wait()